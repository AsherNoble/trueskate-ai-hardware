// Loop-timing benchmark for the index axis.
//
// Measurement tool, not controller firmware -- it lives in bench/ and builds
// as env:loop_timing so it can never be mistaken for src/.
//
// Safety matches the main firmware exactly: motor disabled at boot, initFOC
// only on 'I', voltage_limit 2 V. Phases A and D need no PSU. Phases B and C
// energise the motor and must not be run until the bench PSU is on at 12 V
// with a 0.5 A limit.
//
// Timing uses ARM_DWT_CYCCNT, the Cortex-M7 cycle counter. The Teensy 4 core
// enables it during startup (startup.c: ARM_DEMCR |= ARM_DEMCR_TRCENA, then
// ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA), so it free-runs with no setup
// here. Cycles convert to microseconds through F_CPU_ACTUAL rather than a
// compile-time F_CPU, so an overclocked or underclocked build still reports
// real time.
//
// Nothing is printed during a collection phase. Every sample goes into
// online stats plus a 1 us-binned histogram, and the report is rendered
// afterwards from the accumulated state.

#include <SimpleFOC.h>

#include "stats.h"

// ---------------------------------------------------------------- hardware

// Same wiring as the main firmware: IN1-3 on 4/5/6, EN on 8, encoder CS 10.
BLDCMotor motor(11, 5.6f);
BLDCDriver3PWM driver(4, 5, 6, 8);
MagneticSensorSPI sensor(AS5048_SPI, 10);

Commander command(Serial);

bool foc_ready = false;

// command.run() is inside the collection loop, so a keystroke mid-phase
// would otherwise re-enter a phase handler and print during collection.
// Phases run to completion (~2 s) and cannot be interrupted.
bool collecting = false;

// ------------------------------------------------------------------ config

constexpr uint32_t ITERATIONS = 20000;
constexpr int SIX_AXES = 6;

// Phase D sweep. Copies of the stock AS5048_SPI config with only
// clock_speed changed -- mode, resolution and registers stay stock.
constexpr long SWEEP_HZ[] = {1000000L, 2000000L, 4000000L, 8000000L};
constexpr int SWEEP_N = sizeof(SWEEP_HZ) / sizeof(SWEEP_HZ[0]);
constexpr uint32_t AGREE_READS = 1000;
constexpr int AGREE_TOLERANCE_COUNTS = 4;
constexpr float COUNTS_PER_REV = 16384.0f;

MagneticSensorSPIConfig_s sweep_cfg[SWEEP_N];
MagneticSensorSPI* sweep_sensor[SWEEP_N] = {nullptr};

// ------------------------------------------------------------------- stats

enum Metric { M_SENSOR, M_LOOPFOC, M_MOVE, M_BODY, M_SIX, M_COUNT };
Stat stats[M_COUNT];

// Cost of the measurement itself: two CYCCNT reads and the add().
uint32_t timing_overhead_cycles = 0;

static inline uint32_t cyc() { return ARM_DWT_CYCCNT; }

void calibrateOverhead() {
  Stat s;
  s.reset("overhead");
  for (uint32_t i = 0; i < 2000; i++) {
    uint32_t t0 = cyc();
    uint32_t t1 = cyc();
    s.add(t1 - t0);
  }
  timing_overhead_cycles = (uint32_t)(s.meanUs() * (F_CPU_ACTUAL / 1.0e6f));
}

// -------------------------------------------------------------- collection

// One collection phase. Every iteration times the four metrics; `six`
// additionally times SIX_AXES back-to-back sensor reads on the single
// sensor, as a stand-in for a six-axis hand sharing one SPI bus.
//
// NOTE: loopFOC() calls sensor->update() internally, so an iteration here
// performs TWO sensor reads -- the explicit one being timed, plus the one
// inside loopFOC(). M_BODY therefore overstates a real controller loop by
// about one sensor read. The report derives the realistic figure.
void collect(uint32_t iterations, bool six) {
  collecting = true;

  stats[M_SENSOR].reset("sensor.update()");
  stats[M_LOOPFOC].reset("motor.loopFOC()");
  stats[M_MOVE].reset("motor.move()");
  stats[M_BODY].reset("whole loop body");
  if (six) stats[M_SIX].reset("6x sensor.update()");

  for (uint32_t i = 0; i < iterations; i++) {
    uint32_t b0 = cyc();

    command.run();

    uint32_t t0 = cyc();
    sensor.update();
    uint32_t t1 = cyc();

    motor.loopFOC();
    uint32_t t2 = cyc();

    motor.move();
    uint32_t t3 = cyc();

    stats[M_SENSOR].add(t1 - t0);
    stats[M_LOOPFOC].add(t2 - t1);
    stats[M_MOVE].add(t3 - t2);
    stats[M_BODY].add(t3 - b0);

    if (six) {
      uint32_t s0 = cyc();
      for (int a = 0; a < SIX_AXES; a++) sensor.update();
      uint32_t s1 = cyc();
      stats[M_SIX].add(s1 - s0);
    }
  }

  collecting = false;
}

// ------------------------------------------------------------------ report

void printStatRow(const Stat& s) {
  if (s.empty()) return;
  Serial.printf("  %-20s %8.2f %8.2f %8.0f %8.0f %8.0f %8.2f  %7lu\n",
                s.name(), s.minUs(), s.meanUs(), s.percentileUs(0.50f),
                s.percentileUs(0.99f), s.percentileUs(0.999f), s.maxUs(),
                (unsigned long)s.overflowCount());
}

void printReport(const char* phase, bool six) {
  Serial.println();
  Serial.printf("=== %s ===\n", phase);
  Serial.printf("  iterations %lu   F_CPU_ACTUAL %lu Hz   timing overhead %lu cycles (%.3f us)\n",
                (unsigned long)stats[M_BODY].count(),
                (unsigned long)F_CPU_ACTUAL,
                (unsigned long)timing_overhead_cycles,
                Stat::cyclesToUs(timing_overhead_cycles));
  Serial.println("  metric                    min     mean      p50      p99    p99.9      max   ovf");
  Serial.println("  ------------------------------------------------------------------------------");
  printStatRow(stats[M_SENSOR]);
  printStatRow(stats[M_LOOPFOC]);
  printStatRow(stats[M_MOVE]);
  printStatRow(stats[M_BODY]);
  if (six) printStatRow(stats[M_SIX]);
  Serial.println("  ------------------------------------------------------------------------------");

  const float body = stats[M_BODY].meanUs();
  const float sens = stats[M_SENSOR].meanUs();
  Serial.printf("  loop rate (as measured)   %8.1f Hz  (mean body %.2f us)\n",
                body > 0 ? 1.0e6f / body : 0.0f, body);
  // The benchmark's extra sensor.update() is not part of a controller loop.
  const float real_body = body - sens;
  Serial.printf("  loop rate (less the extra sensor read) %8.1f Hz  (%.2f us)\n",
                real_body > 0 ? 1.0e6f / real_body : 0.0f, real_body);
  if (six) {
    Serial.printf("  6x sensor read mean       %8.2f us\n", stats[M_SIX].meanUs());
  }
  Serial.println();
}

// ------------------------------------------------------------------ phases

void phaseA(char* cmd) {
  (void)cmd;
  if (collecting) return;
  Serial.println();
  Serial.println("A: sensor only, motor disabled. No PSU needed. Collecting...");
  motor.disable();
  collect(ITERATIONS, true);
  printReport("PHASE A -- sensor only, motor disabled", true);
}

void phaseB(char* cmd) {
  (void)cmd;
  if (collecting) return;
  if (!foc_ready) {
    Serial.println("B: run 'I' first (needs the PSU on)");
    return;
  }
  Serial.println();
  Serial.println("B: torque mode, T0.3, hold the shaft still. Collecting...");
  motor.controller = MotionControlType::torque;
  motor.target = 0.3f;
  motor.enable();
  collect(ITERATIONS, false);
  motor.disable();
  motor.target = 0;
  printReport("PHASE B -- torque mode, target 0.3 V, shaft held", false);
}

void phaseC(char* cmd) {
  (void)cmd;
  if (collecting) return;
  if (!foc_ready) {
    Serial.println("C: run 'I' first (needs the PSU on)");
    return;
  }
  Serial.println();
  Serial.println("C: velocity mode, 5 rad/s, free spinning. Collecting...");
  motor.controller = MotionControlType::velocity;
  motor.target = 5.0f;
  motor.enable();
  collect(ITERATIONS, false);
  motor.disable();
  motor.target = 0;
  motor.controller = MotionControlType::torque;
  printReport("PHASE C -- velocity mode, 5 rad/s, free spinning", false);
}

// Raw counts from a sensor's mechanical angle, 0..16383.
static float rawCounts(MagneticSensorSPI* s) {
  return s->getMechanicalAngle() / _2PI * COUNTS_PER_REV;
}

// Shortest signed distance between two counts on a 16384-count circle.
static float countDelta(float a, float b) {
  float d = a - b;
  while (d > COUNTS_PER_REV / 2) d -= COUNTS_PER_REV;
  while (d < -COUNTS_PER_REV / 2) d += COUNTS_PER_REV;
  return d;
}

void phaseD(char* cmd) {
  (void)cmd;
  if (collecting) return;
  collecting = true;
  Serial.println();
  Serial.println("D: SPI clock sweep, motor disabled. Keep the shaft still. Collecting...");
  motor.disable();

  // Reference pass: the mean of AGREE_READS at 1 MHz, taken before any
  // speed is judged. Every speed INCLUDING 1 MHz is then compared against
  // it, so the 1 MHz row reports the sensor's own noise floor rather than
  // a vacuous self-comparison.
  double ref_sum = 0;
  for (uint32_t r = 0; r < AGREE_READS; r++) {
    sweep_sensor[0]->update();
    ref_sum += rawCounts(sweep_sensor[0]);
  }
  const float reference = (float)(ref_sum / AGREE_READS);

  // A faster clock "disagrees" only when it is worse than the sensor is at
  // 1 MHz. Judging it against a fixed +/-4 counts conflates bus corruption
  // with ordinary jitter, which is what the first run did.
  float tolerance = (float)AGREE_TOLERANCE_COUNTS;
  float baseline_dev = 0.0f;

  Serial.println();
  Serial.println("=== PHASE D -- SPI clock sweep, sensor.update() only ===");
  Serial.printf("  reference (1 MHz, %lu reads): %.1f counts\n",
                (unsigned long)AGREE_READS, reference);
  Serial.println("  clock     min     mean      p50      p99    p99.9      max   max_dev  bad/1000  tol");
  Serial.println("  --------------------------------------------------------------------------------");

  for (int i = 0; i < SWEEP_N; i++) {
    MagneticSensorSPI* s = sweep_sensor[i];

    // Agreement check first, so a speed that reads wrong is reported even
    // if its timing looks fine.
    float max_dev = 0.0f;
    uint32_t bad = 0;
    for (uint32_t r = 0; r < AGREE_READS; r++) {
      s->update();
      float dev = fabsf(countDelta(rawCounts(s), reference));
      if (dev > max_dev) max_dev = dev;
      if (dev > tolerance) bad++;
    }

    if (i == 0) {
      // Widen the tolerance to the measured noise floor if it exceeds the
      // nominal +/-4, and re-score this row against it.
      baseline_dev = max_dev;
      if (baseline_dev > tolerance) {
        tolerance = baseline_dev;
        bad = 0;
      }
    }

    Stat t;
    t.reset("sweep");
    for (uint32_t k = 0; k < ITERATIONS; k++) {
      uint32_t t0 = cyc();
      s->update();
      uint32_t t1 = cyc();
      t.add(t1 - t0);
    }

    Serial.printf("  %4ld MHz %7.2f %8.2f %8.0f %8.0f %8.0f %8.2f %9.1f %9lu %4.1f%s\n",
                  SWEEP_HZ[i] / 1000000L, t.minUs(), t.meanUs(),
                  t.percentileUs(0.50f), t.percentileUs(0.99f),
                  t.percentileUs(0.999f), t.maxUs(), max_dev,
                  (unsigned long)bad, tolerance,
                  bad ? "   <== DISAGREES" : "");

    if (bad) {
      Serial.printf("  stopping the sweep: %ld MHz deviates by up to %.1f counts, "
                    "worse than the 1 MHz noise floor of %.1f\n",
                    SWEEP_HZ[i] / 1000000L, max_dev, baseline_dev);
      break;
    }
  }

  Serial.println("  --------------------------------------------------------------------------------");
  Serial.printf("  1 MHz noise floor: %.1f counts. Tolerance used: %.1f counts.\n",
                baseline_dev, tolerance);
  Serial.println();

  collecting = false;
}

void doInitFOC(char* cmd) {
  (void)cmd;
  if (collecting) return;
  if (foc_ready) {
    Serial.println("I: initFOC already done");
    return;
  }
  Serial.println();
  Serial.println("I: running initFOC() -- the shaft will move");
  motor.enable();
  int ok = motor.initFOC();
  motor.disable();
  if (ok) {
    foc_ready = true;
    motor.target = 0;
    Serial.println("I: initFOC OK. Motor disabled, target 0.");
    Serial.printf("I: zero_electric_angle %.4f  sensor_direction %d  PP check %s\n",
                  motor.zero_electric_angle, (int)motor.sensor_direction,
                  motor.pp_check_result ? "OK" : "FAIL");
  } else {
    Serial.println("I: initFOC FAILED. Motor disabled.");
  }
  Serial.println();
}

void doStop(char* cmd) {
  (void)cmd;
  if (collecting) return;
  motor.disable();
  motor.target = 0;
  motor.controller = MotionControlType::torque;
  Serial.println("S: motor disabled, target 0, torque mode");
}

// -------------------------------------------------------------------- init

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {
  }

  SimpleFOCDebug::enable(&Serial);
  Serial.println("loop_timing benchmark / teensy41");

  sensor.init();
  motor.linkSensor(&sensor);

  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;
  driver.init();
  motor.linkDriver(&driver);

  motor.foc_modulation = FOCModulationType::SinePWM;
  motor.controller = MotionControlType::torque;
  motor.voltage_limit = 2;
  motor.current_limit = 0.3;
  motor.voltage_sensor_align = 1.5;

  motor.init();
  motor.disable();

  // Sweep sensors: stock AS5048_SPI with only clock_speed changed. Built
  // here so phase D never touches the sensor the motor is linked to.
  for (int i = 0; i < SWEEP_N; i++) {
    sweep_cfg[i] = AS5048_SPI;
    sweep_cfg[i].clock_speed = SWEEP_HZ[i];
    sweep_sensor[i] = new MagneticSensorSPI(sweep_cfg[i], 10);
    sweep_sensor[i]->init();
  }

  calibrateOverhead();

  command.add('I', doInitFOC, "run initFOC (needs PSU)");
  command.add('A', phaseA, "phase A: sensor only, no PSU");
  command.add('B', phaseB, "phase B: torque, held");
  command.add('C', phaseC, "phase C: velocity 5 rad/s");
  command.add('D', phaseD, "phase D: SPI clock sweep");
  command.add('S', doStop, "stop and disable");

  Serial.println();
  Serial.printf("F_CPU_ACTUAL %lu Hz, timing overhead %lu cycles (%.3f us)\n",
                (unsigned long)F_CPU_ACTUAL,
                (unsigned long)timing_overhead_cycles,
                Stat::cyclesToUs(timing_overhead_cycles));
  Serial.println("Motor DISABLED. A and D need no PSU; B and C energise the motor.");
  Serial.println("Commands: A B C D, I = initFOC, S = stop");
  Serial.println();
}

void loop() {
  // Idle between phases: keep the angle fresh, stay dark.
  command.run();
  if (!foc_ready) {
    sensor.update();
  } else {
    motor.loopFOC();
    motor.move();
  }
}
