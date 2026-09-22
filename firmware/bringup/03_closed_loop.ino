// BRINGUP ARCHIVE -- unchanged from ~/teensy. First closed loop: initFOC on demand, pole-pair check OK at 11, 720 deg at 60 rpm. Ported to firmware/src.
// 03_closed_loop.ino
//
// GM3506 + SimpleFOC Mini + AS5048A on SPI0.
// Teensy 4.1: IN1 4, IN2 5, IN3 6, EN 8. Sensor CS 10, CLK 13,
// MOSI 11, MISO 12.
//
// Phase 1 established: stock AS5048_SPI (SPI_MODE1 @ 1MHz) reads the
// encoder correctly. Do not substitute a custom config.
//
// initFOC() is NOT called from setup(). It spins the shaft, so it needs
// the PSU live, and the PSU is off at flash time. Send 'I' to run it.
//
// Build with:
//   --build-property compiler.cpp.extra_flags=-DSIMPLEFOC_TEENSY4_FORCE_CENTER_ALIGNED_3PWM

#include <SimpleFOC.h>

BLDCMotor motor(11, 5.6f);
BLDCDriver3PWM driver(4, 5, 6, 8);
MagneticSensorSPI sensor(AS5048_SPI, 10);

Commander command(Serial);

// Set once 'I' has completed. Until then loopFOC()/move() must not run:
// without an alignment they would commutate against an unknown offset.
bool foc_ready = false;

// The driver stays disabled until a nonzero target is set, so nothing
// is energised while the bench is being set up.
bool driver_enabled = false;

void doTarget(char* cmd) { command.scalar(&motor.target, cmd); }

// 0 = torque, 1 = velocity, 2 = angle. Torque only, until the rest is
// proven out.
void doMotion(char* cmd) {
  float v;
  command.scalar(&v, cmd);
  switch ((int)v) {
    case 0: motor.controller = MotionControlType::torque;   break;
    case 1: motor.controller = MotionControlType::velocity; break;
    case 2: motor.controller = MotionControlType::angle;    break;
    default: Serial.println("M: 0=torque 1=velocity 2=angle"); return;
  }
  Serial.printf("M: controller = %d\n", (int)v);
}

void doInitFOC(char* cmd) {
  (void)cmd;

  if (foc_ready) {
    Serial.println("I: initFOC already done");
    return;
  }

  Serial.println();
  Serial.println("I: running initFOC() -- the shaft will move");

  motor.enable();
  int ok = motor.initFOC();

  if (ok) {
    foc_ready = true;
    motor.target = 0;
    motor.disable();        // back to idle until a target is set
    driver_enabled = false;
    Serial.println("I: initFOC OK. Motor disabled, target 0.");
    Serial.printf("I: zero_electric_angle %.4f  sensor_direction %d\n",
                  motor.zero_electric_angle, (int)motor.sensor_direction);
    Serial.printf("I: PP check result: %s\n",
                  motor.pp_check_result ? "OK" : "FAIL");
  } else {
    motor.disable();
    driver_enabled = false;
    Serial.println("I: initFOC FAILED. Motor disabled.");
  }
  Serial.println();
}


// 'G' — closed-loop move of 720 deg at 60 rpm.
//
// Angle mode with velocity_limit = 2PI rad/s (60 rpm). P_angle.limit is
// set from velocity_limit, so the angle controller saturates at 60 rpm
// for most of the travel and eases in at the end. Runs the FOC loop
// inline rather than leaving it to loop(), so the move is self-contained
// and always ends with the motor disabled.
void doGo(char* cmd) {
  (void)cmd;

  if (!foc_ready) {
    Serial.println("G: run I first");
    return;
  }

  const float TRAVEL   = 4.0f * PI;   // 720 deg
  const float RPM60    = _2PI;        // 60 rpm in rad/s
  const uint32_t LIMIT = 15000;       // ms; nominal move is ~2 s

  motor.controller = MotionControlType::angle;
  motor.updateVelocityLimit(RPM60);

  motor.loopFOC();          // refresh shaft_angle; driver still disabled
  float start = motor.shaft_angle;
  motor.target = start + TRAVEL;

  Serial.printf("G: %.1f deg at 60 rpm, from %.2f to %.2f rad\n",
                TRAVEL * 180.0f / PI, start, motor.target);

  motor.enable();
  driver_enabled = true;

  uint32_t t0 = millis(), lastPrint = 0;
  bool arrived = false;

  while (millis() - t0 < LIMIT) {
    motor.loopFOC();
    motor.move();

    if (millis() - lastPrint >= 250) {
      lastPrint = millis();
      Serial.printf("  t %5lu ms  pos %8.2f deg  vel %6.1f rpm  Uq %5.2f V\n",
                    millis() - t0,
                    (motor.shaft_angle - start) * 180.0f / PI,
                    motor.shaft_velocity * 60.0f / _2PI,
                    motor.voltage.q);
    }

    if (fabs(motor.target - motor.shaft_angle) < 0.02f &&
        fabs(motor.shaft_velocity) < 0.20f) { arrived = true; break; }
  }

  uint32_t elapsed = millis() - t0;
  float travelled = (motor.shaft_angle - start) * 180.0f / PI;

  motor.disable();
  driver_enabled = false;

  // Return to the idle state: torque mode, zero target, nothing energised.
  motor.controller = MotionControlType::torque;
  motor.target = 0;

  Serial.printf("G: %s after %lu ms, travelled %.2f deg (mean %.1f rpm)\n",
                arrived ? "arrived" : "TIMEOUT", elapsed, travelled,
                (travelled / 360.0f) / (elapsed / 60000.0f));
  Serial.println("G: motor disabled, back to torque mode, target 0");
  Serial.println();
}

void setup() {
  Serial.begin(115200);

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  SimpleFOCDebug::enable(&Serial);

  Serial.println("03_closed_loop");

  sensor.init();
  motor.linkSensor(&sensor);

  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;
  driver.init();
  motor.linkDriver(&driver);

  motor.foc_modulation = FOCModulationType::SinePWM;
  motor.controller = MotionControlType::torque;  // voltage torque mode

  motor.voltage_limit = 2;
  motor.current_limit = 0.3;
  motor.voltage_sensor_align = 1.5;

  motor.init();
  motor.disable();               // nothing energised until 'I' / a target
  driver_enabled = false;

  command.add('T', doTarget, "target");
  command.add('M', doMotion, "motion mode 0/1/2");
  command.add('I', doInitFOC, "run initFOC");
  command.add('G', doGo, "720 deg at 60 rpm");

  Serial.println();
  Serial.println("setup() complete. Motor DISABLED, PSU may still be off.");
  Serial.println("Turn the PSU on (12V, 0.5A), then send 'I' to align.");
  Serial.println("Commands: I = initFOC, T<volts> = target, M0/M1/M2 = mode");
  Serial.println();
}

void loop() {
  command.run();

  if (!foc_ready) {
    sensor.update();             // keep the angle fresh for monitoring
    return;                      // no commutation before alignment
  }

  // Energise only while a nonzero target is asked for.
  bool want = (motor.controller == MotionControlType::torque)
              && (motor.target != 0.0f);
  if (want != driver_enabled) {
    if (want) motor.enable(); else motor.disable();
    driver_enabled = want;
    Serial.printf("driver %s\n", want ? "ENABLED" : "disabled");
  }

  motor.loopFOC();               // 2.4.0 needs this called explicitly
  motor.move();
}
