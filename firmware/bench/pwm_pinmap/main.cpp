// Can six SimpleFOC 3PWM axes coexist on one Teensy 4.1?
//
// Measurement tool. NO MOTORS, PSU OFF. Every EN line is driven low and
// held there, so even with a driver attached nothing reaches a motor.
//
// Teensy 4.1 has only 14 FlexPWM submodules reachable by a channel-A or -B
// pin. Six independent center-aligned axes would need 18, so at least two
// axes must share submodules with another axis. This sketch builds all six
// drivers in order, reports which took the center-aligned path and which
// fell back to analogWrite, and parks each of the 18 pins at a distinct
// fixed duty so a voltmeter can show whether a later axis clobbered an
// earlier one's timer.
//
// Detection is programmatic, not text-scraping: _configure3PWM stores a
// Teensy4DriverParams in TeensyDriverParams::additional_params only on the
// center-aligned path, and _writeDutyCycle3PWM dispatches on that pointer
// being non-null.
//
// Pin map rationale and the expected collisions are in
// docs/pwm-pinmap.md.

#include <SimpleFOC.h>

// Mirrors of the library's parameter structs. Declared locally rather than
// including teensy4_mcu.h, which *defines* pwm_pin_info[] in the header and
// would collide with the core's own copy.
typedef struct {
  int pins[6];
  long pwm_frequency;
  void* additional_params;
} TeensyParamsMirror;

typedef struct {
  IMXRT_FLEXPWM_t* flextimers[3];
  int submodules[3];
  int channels[6];
  float dead_zone;
} Teensy4ParamsMirror;

// ------------------------------------------------------------------ config

struct AxisPins {
  const char* name;
  int a, b, c, en;
};

// Axes 1-3 as already assigned, except axis 1's EN moves 8 -> 30: pin 8 is
// FlexPWM1_3_A and is needed as a phase, and without it there are only
// eight free PWM pins for the nine that axes 4-6 require.
const AxisPins AXES[] = {
  {"axis1", 4,  5,  6,  30},
  {"axis2", 2,  22, 23, 14},
  {"axis3", 7,  36, 29, 16},
  {"axis4", 24, 15, 25, 17},
  {"axis5", 3,  33, 37, 20},
  {"axis6", 8,  9,  28, 21},
};
constexpr int N_AXES = sizeof(AXES) / sizeof(AXES[0]);

// setPwm() takes volts and divides by voltage_power_supply. Setting both
// supply and limit to 100 makes the argument a duty percentage directly.
constexpr float PWM_SCALE = 100.0f;

// 18 distinct duties, 5% to 90% in 5% steps, assigned in pin order.
constexpr float DUTY_STEP = 5.0f;

BLDCDriver3PWM* drivers[N_AXES] = {nullptr};

// ------------------------------------------------------------------ report

int flexpwmIndex(IMXRT_FLEXPWM_t* p) {
  if (p == &IMXRT_FLEXPWM1) return 1;
  if (p == &IMXRT_FLEXPWM2) return 2;
  if (p == &IMXRT_FLEXPWM3) return 3;
  if (p == &IMXRT_FLEXPWM4) return 4;
  return -1;
}

const char* channelName(int ch) {
  return ch == 0 ? "X" : ch == 1 ? "A" : ch == 2 ? "B" : "?";
}

bool isCenterAligned(BLDCDriver3PWM* d) {
  if (!d || !d->params) return false;
  TeensyParamsMirror* p = (TeensyParamsMirror*)d->params;
  return p->additional_params != nullptr;
}

void reportAxis(int i) {
  BLDCDriver3PWM* d = drivers[i];
  const AxisPins& ax = AXES[i];

  if (!d || !d->params) {
    Serial.printf("  %-6s pins %2d %2d %2d   INIT FAILED\n",
                  ax.name, ax.a, ax.b, ax.c);
    return;
  }

  // Mirror sanity: pwm_frequency must read back as the configured 25 kHz.
  // If it does not, the struct layout is wrong and additional_params is
  // being read from the wrong offset.
  {
    TeensyParamsMirror* p = (TeensyParamsMirror*)d->params;
    Serial.printf("  %-6s [raw: pins %d %d %d  freq %ld  addl %p]\n",
                  ax.name, p->pins[0], p->pins[1], p->pins[2],
                  p->pwm_frequency, p->additional_params);
  }

  if (!isCenterAligned(d)) {
    Serial.printf("  %-6s pins %2d %2d %2d   FALLBACK (edge-aligned, analogWrite)\n",
                  ax.name, ax.a, ax.b, ax.c);
    return;
  }

  TeensyParamsMirror* p = (TeensyParamsMirror*)d->params;
  Teensy4ParamsMirror* t = (Teensy4ParamsMirror*)p->additional_params;

  Serial.printf("  %-6s pins %2d %2d %2d   CENTER-ALIGNED  ",
                ax.name, ax.a, ax.b, ax.c);
  for (int k = 0; k < 3; k++) {
    Serial.printf("PWM%d_%d_%s%s", flexpwmIndex(t->flextimers[k]),
                  t->submodules[k], channelName(t->channels[k]),
                  k < 2 ? " " : "");
  }
  // pinC's submodule is the master; the other two are XBAR-synced to it.
  Serial.printf("   master PWM%d_%d\n", flexpwmIndex(t->flextimers[2]),
                t->submodules[2]);
}

// -------------------------------------------------------------------- init

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 4000) {
  }

  SimpleFOCDebug::enable(&Serial);

  Serial.println();
  Serial.println("pwm_pinmap: 6 x BLDCDriver3PWM on one Teensy 4.1");
  Serial.println("NO MOTORS. PSU OFF. All EN lines held low.");
  Serial.println();

  // Park every EN low before any driver touches a pin.
  for (int i = 0; i < N_AXES; i++) {
    pinMode(AXES[i].en, OUTPUT);
    digitalWrite(AXES[i].en, LOW);
  }

  Serial.println("--- init, in order ---");
  for (int i = 0; i < N_AXES; i++) {
    Serial.printf("\n[%s] init pins %d %d %d, EN %d\n", AXES[i].name,
                  AXES[i].a, AXES[i].b, AXES[i].c, AXES[i].en);
    drivers[i] = new BLDCDriver3PWM(AXES[i].a, AXES[i].b, AXES[i].c, AXES[i].en);
    drivers[i]->voltage_power_supply = PWM_SCALE;
    drivers[i]->voltage_limit = PWM_SCALE;
    if (!drivers[i]->init()) {
      Serial.printf("[%s] driver init FAILED\n", AXES[i].name);
    }
    drivers[i]->disable();          // EN back low; init() may have raised it
    digitalWrite(AXES[i].en, LOW);
  }

  Serial.println();
  Serial.println("--- which path each axis took ---");
  for (int i = 0; i < N_AXES; i++) reportAxis(i);

  // Distinct duty per pin, applied after every axis is configured, so the
  // readings reflect the final state of the timers.
  Serial.println();
  Serial.println("--- expected pin voltages (duty x 3.3V, DC meter to GND) ---");
  Serial.println("  axis   pin  duty     expect");
  Serial.println("  ------------------------------");
  for (int i = 0; i < N_AXES; i++) {
    const float da = (i * 3 + 1) * DUTY_STEP;
    const float db = (i * 3 + 2) * DUTY_STEP;
    const float dc = (i * 3 + 3) * DUTY_STEP;
    drivers[i]->setPwm(da, db, dc);
    const int pins[3] = {AXES[i].a, AXES[i].b, AXES[i].c};
    const float duties[3] = {da, db, dc};
    for (int k = 0; k < 3; k++) {
      Serial.printf("  %-6s %3d  %4.0f%%   %5.3f V\n", AXES[i].name, pins[k],
                    duties[k], duties[k] / 100.0f * 3.3f);
    }
  }
  Serial.println("  ------------------------------");
  Serial.println();
  Serial.println("Duties are held. Meter each pin against GND.");
  Serial.println("A pin reading a voltage other than its row means a later");
  Serial.println("axis reconfigured a timer an earlier axis was using.");
  Serial.println();
}

void loop() {
  // Nothing to do: the duties are latched in hardware. Re-asserting them
  // here would hide a clobber that happened at init.
  delay(1000);
}
