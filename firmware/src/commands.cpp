#include "commands.h"

#include "axis.h"

namespace {

Axis* g_axis = nullptr;
Commander* g_commander = nullptr;

void cmdTarget(char* cmd) {
  if (!g_axis || !g_commander) return;
  float v = g_axis->targetGet();
  g_commander->scalar(&v, cmd);
  g_axis->targetSet(v);
}

void cmdMotion(char* cmd) {
  if (!g_axis || !g_commander) return;
  float v = 0;
  g_commander->scalar(&v, cmd);
  switch ((int)v) {
    case 0: g_axis->setMotionMode(MotionControlType::torque); break;
    case 1: g_axis->setMotionMode(MotionControlType::velocity); break;
    case 2: g_axis->setMotionMode(MotionControlType::angle); break;
    default:
      Serial.println("M: 0=torque 1=velocity 2=angle");
      return;
  }
  Serial.printf("M: controller = %d\n", (int)v);
}

void cmdInitFOC(char* cmd) {
  (void)cmd;
  if (!g_axis) return;

  if (g_axis->ready()) {
    Serial.println("I: initFOC already done");
    return;
  }

  Serial.println();
  Serial.println("I: running initFOC() -- the shaft will move");

  if (g_axis->initFOC()) {
    Serial.println("I: initFOC OK. Motor disabled, target 0.");
    Serial.printf("I: zero_electric_angle %.4f  sensor_direction %d\n",
                  g_axis->zeroElectricAngle(), g_axis->sensorDirection());
    Serial.printf("I: PP check result: %s\n",
                  g_axis->poleCheckOk() ? "OK" : "FAIL");
  } else {
    Serial.println("I: initFOC FAILED. Motor disabled.");
  }
  Serial.println();
}

void cmdGo(char* cmd) {
  (void)cmd;
  if (!g_axis) return;

  if (!g_axis->ready()) {
    Serial.println("G: run I first");
    return;
  }

  const float travel = 4.0f * PI;   // 720 deg
  Serial.println("G: 720.0 deg at 60 rpm");

  const uint32_t t0 = millis();
  const bool arrived = g_axis->moveBy(travel, 60.0f, 15000);
  const uint32_t elapsed = millis() - t0;

  Serial.printf("G: %s after %lu ms\n", arrived ? "arrived" : "TIMEOUT",
                (unsigned long)elapsed);
  Serial.println("G: motor disabled, back to torque mode, target 0");
  Serial.println();
}

}  // namespace

void commandsBegin(Commander& commander, Axis& axis) {
  g_axis = &axis;
  g_commander = &commander;
  commander.add('I', cmdInitFOC, "run initFOC");
  commander.add('T', cmdTarget, "target (volts in voltage torque mode)");
  commander.add('M', cmdMotion, "motion mode 0/1/2");
  commander.add('G', cmdGo, "720 deg at 60 rpm");
}
