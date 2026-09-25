// Flick-and-reset test on axis 1.
//
// The question: is voltage-mode FOC without current sensing good enough for
// a finger, or do we need per-motor controllers with current control?
//
// Motor free, no load. Safety matches the main firmware: motor disabled at
// boot, initFOC only on 'I', driver energised only for the duration of a
// run, disabled again afterwards.
//
// Logging is to a RAM buffer, never live serial -- printing inside the
// control loop would dominate the timing it is trying to measure. The
// buffer lives in DMAMEM (RAM2) because 14000 samples x 24 B is 336 KB.
// Teensy native USB ignores the baud rate, so a full CSV dump takes about
// a second, not a minute.
//
// Commands:
//   I         initFOC (moves the shaft; PSU must be on)
//   V<volts>  set motor voltage_limit, 2.0 to 6.0
//   S         step run: 0 -> +90 deg -> 0
//   F         one flick: +60 deg and straight back, as fast as it will go
//   R         20 flicks back to back
//   D         re-dump the last run's CSV
//   X         stop: disable, target 0

#include <SimpleFOC.h>

// Axis 1, exactly as the main firmware wires it.
BLDCMotor motor(11, 5.6f);
BLDCDriver3PWM driver(4, 5, 6, 8);
MagneticSensorSPI sensor(AS5048_SPI, 10);

Commander command(Serial);

bool foc_ready = false;
bool busy = false;   // command.run() is inside the run loops; block re-entry

// ------------------------------------------------------------------ config

constexpr float V_MIN = 2.0f;
constexpr float V_MAX = 6.0f;

constexpr float STEP_DEG = 90.0f;
constexpr float FLICK_DEG = 60.0f;

// Angle mode is cascaded: P_angle output is a velocity setpoint capped by
// velocity_limit, and PID_velocity output is a voltage capped by
// voltage_limit. Setting velocity_limit high on purpose, so that VOLTAGE is
// the binding constraint -- that is what "as fast as possible" means here,
// and it is what makes Uq saturation the thing being measured.
// Set by 'L'. P_angle's output is a velocity setpoint capped by this, so it
// must clear P_angle x max error or the sweep measures the cap, not the gain.
// Peak demand is P_angle x 1.047 rad (60 deg): 41.9 / 83.8 / 167.6 rad/s at
// P_angle 40 / 80 / 160. 200 rad/s clears the largest by 19% and is one value
// across the whole sweep, so P_angle stays the only variable. It is also far
// above what the motor can physically reach, so the cap cannot bind either way.
float vel_limit = 200.0f;               // rad/s

constexpr uint32_t STEP_DWELL_MS  = 1000;
constexpr uint32_t FLICK_SEG_MAX_MS = 400;   // cap per out/back segment
constexpr uint32_t FLICK_REST_MS  = 250;
constexpr int      FLICK_REPEATS  = 20;

// "Arrived" for the purpose of turning a flick around. Deliberately loose:
// this is a flick, not a settle, and waiting for a tight band would make
// the turnaround time a function of the tolerance.
constexpr float ARRIVE_RAD = 0.02f;      // ~1.15 deg
constexpr float ARRIVE_VEL = 0.5f;       // rad/s

constexpr uint32_t LOG_PERIOD_US = 1000;  // 1 kHz

// ------------------------------------------------------------------ logging

enum Phase : uint8_t { PH_IDLE = 0, PH_OUT = 1, PH_BACK = 2, PH_DWELL = 3 };

struct Sample {
  uint32_t t_us;
  float target;
  float angle;
  float velocity;
  float uq;
  uint8_t phase;
  uint8_t flick;
};

constexpr uint32_t MAX_SAMPLES = 14000;   // 14 s at 1 kHz
DMAMEM Sample log_buf[MAX_SAMPLES];

uint32_t n_samples = 0;
uint32_t log_t0_us = 0;
uint32_t next_log_us = 0;
bool logging = false;

const char* last_run = "none";
float last_run_voltage = 0;

uint8_t cur_phase = PH_IDLE;
uint8_t cur_flick = 0;

void logStart() {
  n_samples = 0;
  log_t0_us = micros();
  next_log_us = log_t0_us;
  logging = true;
}

void logStop() { logging = false; }

inline void logMaybe() {
  if (!logging || n_samples >= MAX_SAMPLES) return;
  const uint32_t now = micros();
  if ((int32_t)(now - next_log_us) < 0) return;
  next_log_us += LOG_PERIOD_US;

  Sample& s = log_buf[n_samples++];
  s.t_us = now - log_t0_us;
  s.target = motor.target;
  s.angle = motor.shaft_angle;
  s.velocity = motor.shaft_velocity;
  s.uq = motor.voltage.q;
  s.phase = cur_phase;
  s.flick = cur_flick;
}

// Which limit was actually active during the strokes? Three mutually
// exclusive states per sample: the velocity cap clipped P_angle's output, Uq
// sat at voltage_limit, or neither and the gain alone set the motion.
void summariseBinding() {
  uint32_t n = 0, v_cap = 0, u_sat = 0, both = 0;
  float peak_vel = 0, peak_uq = 0;

  for (uint32_t i = 0; i < n_samples; i++) {
    const Sample& s = log_buf[i];
    if (s.phase != PH_OUT && s.phase != PH_BACK) continue;
    n++;
    const float demand = fabsf(motor.P_angle.P * (s.target - s.angle));
    const bool vc = demand >= vel_limit * 0.98f;
    const bool us = fabsf(s.uq) >= last_run_voltage * 0.98f;
    if (vc && us) both++;
    else if (vc) v_cap++;
    else if (us) u_sat++;
    if (fabsf(s.velocity) > peak_vel) peak_vel = fabsf(s.velocity);
    if (fabsf(s.uq) > peak_uq) peak_uq = fabsf(s.uq);
  }
  if (!n) return;

  const float pv = 100.0f * v_cap / n, pu = 100.0f * u_sat / n,
              pb = 100.0f * both / n;
  const float pn = 100.0f - pv - pu - pb;

  Serial.printf("# binding: velocity_cap %.1f%%  Uq_sat %.1f%%  both %.1f%%  neither %.1f%%\n",
                pv, pu, pb, pn);
  Serial.printf("# peak_vel %.1f rpm  peak_Uq %.3f V  stroke_samples %lu\n",
                peak_vel * 60.0f / _2PI, peak_uq, (unsigned long)n);
  const char* verdict = (pv + pb > 5.0f) ? "VELOCITY CAP"
                      : (pu + pb > 5.0f) ? "Uq SATURATION"
                                         : "NEITHER - gain-limited";
  Serial.printf("# binding limit: %s\n", verdict);
}

void dumpCsv() {
  Serial.println();
  Serial.printf("# run=%s voltage_limit=%.2f velocity_limit=%.1f p_angle=%.1f samples=%lu rate=%luHz\n",
                last_run, last_run_voltage, vel_limit, motor.P_angle.P,
                (unsigned long)n_samples, (unsigned long)(1000000UL / LOG_PERIOD_US));
  Serial.println("t_ms,phase,flick,target_deg,angle_deg,vel_rpm,uq_v");
  for (uint32_t i = 0; i < n_samples; i++) {
    const Sample& s = log_buf[i];
    Serial.printf("%.3f,%u,%u,%.4f,%.4f,%.3f,%.4f\n",
                  s.t_us / 1000.0f, s.phase, s.flick,
                  s.target * 180.0f / PI, s.angle * 180.0f / PI,
                  s.velocity * 60.0f / _2PI, s.uq);
  }
  summariseBinding();
  Serial.printf("# end %s\n", last_run);
  Serial.println();
}

// ------------------------------------------------------------ run primitives

// Run the FOC loop until `until_us` has elapsed, logging as we go.
void spinFor(uint32_t duration_ms) {
  const uint32_t t0 = millis();
  while (millis() - t0 < duration_ms) {
    motor.loopFOC();
    motor.move();
    logMaybe();
  }
}

// Run until arrived or the cap expires. Returns ms elapsed.
uint32_t spinUntilArrived(uint32_t cap_ms) {
  const uint32_t t0 = millis();
  while (millis() - t0 < cap_ms) {
    motor.loopFOC();
    motor.move();
    logMaybe();
    if (fabsf(motor.target - motor.shaft_angle) < ARRIVE_RAD &&
        fabsf(motor.shaft_velocity) < ARRIVE_VEL) {
      break;
    }
  }
  return millis() - t0;
}

void beginRun(const char* name) {
  motor.controller = MotionControlType::angle;
  motor.updateVelocityLimit(vel_limit);

  motor.loopFOC();                 // refresh shaft_angle while still disabled
  motor.target = motor.shaft_angle;

  last_run = name;
  last_run_voltage = motor.voltage_limit;
  cur_phase = PH_IDLE;
  cur_flick = 0;

  motor.enable();
  logStart();
}

void endRun() {
  logStop();
  motor.disable();
  motor.target = 0;
  motor.controller = MotionControlType::torque;
  cur_phase = PH_IDLE;
}

// ------------------------------------------------------------------ commands

void doStep(char* cmd) {
  (void)cmd;
  if (busy) return;
  if (!foc_ready) { Serial.println("S: run I first"); return; }
  busy = true;

  Serial.printf("\nS: step run, +%.0f deg and back, voltage_limit %.2f V\n",
                STEP_DEG, motor.voltage_limit);

  beginRun("step");
  const float home = motor.target;

  cur_phase = PH_DWELL;
  spinFor(100);                                  // baseline before the step

  cur_phase = PH_OUT;
  motor.target = home + STEP_DEG * PI / 180.0f;
  spinFor(STEP_DWELL_MS);

  cur_phase = PH_BACK;
  motor.target = home;
  spinFor(STEP_DWELL_MS);

  endRun();
  dumpCsv();
  busy = false;
}

// One flick: out and straight back. No dwell at the far end -- the turnaround
// is commanded the moment the outbound segment ends.
void oneFlick(float home, uint8_t index) {
  cur_flick = index;

  cur_phase = PH_OUT;
  motor.target = home + FLICK_DEG * PI / 180.0f;
  spinUntilArrived(FLICK_SEG_MAX_MS);

  cur_phase = PH_BACK;
  motor.target = home;
  spinUntilArrived(FLICK_SEG_MAX_MS);

  cur_phase = PH_DWELL;
  spinFor(FLICK_REST_MS);
}

void doFlick(char* cmd) {
  (void)cmd;
  if (busy) return;
  if (!foc_ready) { Serial.println("F: run I first"); return; }
  busy = true;

  Serial.printf("\nF: single flick, +%.0f deg out and back, voltage_limit %.2f V\n",
                FLICK_DEG, motor.voltage_limit);

  beginRun("flick");
  const float home = motor.target;
  cur_phase = PH_DWELL;
  spinFor(100);
  oneFlick(home, 1);

  endRun();
  dumpCsv();
  busy = false;
}

void doRepeat(char* cmd) {
  (void)cmd;
  if (busy) return;
  if (!foc_ready) { Serial.println("R: run I first"); return; }
  busy = true;

  Serial.printf("\nR: %d flicks back to back, voltage_limit %.2f V\n",
                FLICK_REPEATS, motor.voltage_limit);

  beginRun("flick20");
  const float home = motor.target;
  cur_phase = PH_DWELL;
  spinFor(100);
  for (int i = 1; i <= FLICK_REPEATS; i++) {
    oneFlick(home, (uint8_t)i);
    if (n_samples >= MAX_SAMPLES) {
      Serial.printf("R: log buffer full after flick %d\n", i);
      break;
    }
  }

  endRun();
  dumpCsv();
  busy = false;
}

void doVoltage(char* cmd) {
  if (busy) return;
  float v = motor.voltage_limit;
  command.scalar(&v, cmd);
  if (v < V_MIN || v > V_MAX) {
    Serial.printf("V: %.2f out of range [%.1f, %.1f]\n", v, V_MIN, V_MAX);
    return;
  }
  // updateVoltageLimit, not a bare assignment: in voltage torque mode this
  // is what also moves PID_velocity.limit, which is what actually bounds
  // the angle controller's output.
  motor.updateVoltageLimit(v);
  Serial.printf("V: voltage_limit %.2f V  (stall current about %.2f A at 5.6 ohm)\n",
                motor.voltage_limit, motor.voltage_limit / 5.6f);
}

void doPAngle(char* cmd) {
  if (busy) return;
  float v = motor.P_angle.P;
  command.scalar(&v, cmd);
  if (v <= 0 || v > 1000) { Serial.printf("P: %.1f out of range\n", v); return; }
  motor.P_angle.P = v;
  Serial.printf("P: P_angle %.1f  (peak velocity demand at 60 deg = %.1f rad/s, "
                "velocity_limit %.1f)\n", v, v * 1.047f, vel_limit);
  if (v * 1.047f >= vel_limit)
    Serial.println("P: WARNING demand exceeds velocity_limit; raise L first");
}

void doVelLimit(char* cmd) {
  if (busy) return;
  float v = vel_limit;
  command.scalar(&v, cmd);
  if (v <= 0 || v > 2000) { Serial.printf("L: %.1f out of range\n", v); return; }
  vel_limit = v;
  motor.updateVelocityLimit(vel_limit);
  Serial.printf("L: velocity_limit %.1f rad/s (%.0f rpm)\n",
                vel_limit, vel_limit * 60.0f / _2PI);
}

void doInitFOC(char* cmd) {
  (void)cmd;
  if (busy) return;
  if (foc_ready) { Serial.println("I: already done"); return; }

  Serial.println("\nI: running initFOC() -- the shaft will move");
  motor.enable();
  int ok = motor.initFOC();
  motor.disable();
  if (ok) {
    foc_ready = true;
    motor.target = 0;
    Serial.printf("I: OK. zero_electric_angle %.4f  dir %d  PP check %s\n",
                  motor.zero_electric_angle, (int)motor.sensor_direction,
                  motor.pp_check_result ? "OK" : "FAIL");
  } else {
    Serial.println("I: initFOC FAILED");
  }
}

void doDump(char* cmd) {
  (void)cmd;
  if (busy) return;
  dumpCsv();
}

void doStop(char* cmd) {
  (void)cmd;
  motor.disable();
  motor.target = 0;
  motor.controller = MotionControlType::torque;
  Serial.println("X: disabled, target 0");
}

// -------------------------------------------------------------------- setup

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {
  }

  SimpleFOCDebug::enable(&Serial);
  Serial.println("flick_test / axis 1");

  sensor.init();
  motor.linkSensor(&sensor);

  driver.voltage_power_supply = 12;
  driver.voltage_limit = V_MAX;      // hard ceiling at the driver
  driver.init();
  motor.linkDriver(&driver);

  motor.foc_modulation = FOCModulationType::SinePWM;
  motor.controller = MotionControlType::torque;
  motor.voltage_limit = V_MIN;
  motor.current_limit = 0.3;         // inert in voltage mode; see docs
  motor.voltage_sensor_align = 1.5;
  motor.velocity_limit = vel_limit;

  motor.init();
  motor.disable();

  command.add('I', doInitFOC, "initFOC");
  command.add('V', doVoltage, "voltage_limit 2..6");
  command.add('P', doPAngle,  "P_angle gain");
  command.add('L', doVelLimit,"velocity_limit rad/s");
  command.add('S', doStep,    "step 90 deg");
  command.add('F', doFlick,   "one flick 60 deg");
  command.add('R', doRepeat,  "20 flicks");
  command.add('D', doDump,    "re-dump CSV");
  command.add('X', doStop,    "stop");

  Serial.printf("\nlog buffer %lu samples at %lu Hz (%lu KB in RAM2)\n",
                (unsigned long)MAX_SAMPLES,
                (unsigned long)(1000000UL / LOG_PERIOD_US),
                (unsigned long)(sizeof(log_buf) / 1024));
  Serial.printf("voltage_limit %.2f V, driver ceiling %.2f V\n",
                motor.voltage_limit, driver.voltage_limit);
  Serial.println("Motor DISABLED. Turn the PSU on, then 'I'.");
  Serial.printf("P_angle %.1f, velocity_limit %.1f rad/s\n",
                motor.P_angle.P, vel_limit);
  Serial.println("Commands: I, V<volts>, P<gain>, L<rad/s>, S, F, R, D, X");
  Serial.println();
}

void loop() {
  command.run();
  if (!foc_ready) {
    sensor.update();
  } else {
    motor.loopFOC();
    motor.move();
  }
}
