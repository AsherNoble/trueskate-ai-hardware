#include "axis.h"

Axis::Axis(const AxisConfig& cfg)
    : cfg_(cfg),
      motor_(cfg.pole_pairs, cfg.phase_resistance),
      driver_(cfg.pin_in1, cfg.pin_in2, cfg.pin_in3, cfg.pin_enable),
      sensor_(AS5048_SPI, cfg.pin_sensor_cs) {}

bool Axis::begin() {
  sensor_.init();
  motor_.linkSensor(&sensor_);

  driver_.voltage_power_supply = cfg_.voltage_power_supply;
  driver_.voltage_limit = cfg_.driver_voltage_limit;
  if (!driver_.init()) return false;
  motor_.linkDriver(&driver_);

  motor_.foc_modulation = FOCModulationType::SinePWM;
  motor_.controller = MotionControlType::torque;  // voltage torque mode

  motor_.voltage_limit = cfg_.motor_voltage_limit;
  motor_.current_limit = cfg_.current_limit;
  motor_.voltage_sensor_align = cfg_.voltage_sensor_align;

  if (!motor_.init()) return false;

  // Nothing energised until initFOC() or an explicit enable.
  motor_.disable();
  driver_enabled_ = false;
  return true;
}

bool Axis::initFOC() {
  if (foc_ready_) return true;

  motor_.enable();
  int ok = motor_.initFOC();

  motor_.disable();
  driver_enabled_ = false;

  if (!ok) return false;

  foc_ready_ = true;
  motor_.target = 0;
  return true;
}

void Axis::enable() {
  motor_.enable();
  driver_enabled_ = true;
}

void Axis::disable() {
  motor_.disable();
  driver_enabled_ = false;
}

void Axis::update() {
  if (!foc_ready_) {
    // Keep the angle fresh for monitoring, but do not commutate: without
    // an alignment the electrical angle is meaningless.
    sensor_.update();
    return;
  }
  motor_.loopFOC();   // SimpleFOC 2.4 does not call this from move()
  motor_.move();
}

bool Axis::moveBy(float travel_rad, float rpm, uint32_t timeout_ms,
                  float tolerance_rad) {
  if (!foc_ready_) return false;

  const float vel_limit = rpm * _2PI / 60.0f;

  motor_.controller = MotionControlType::angle;
  motor_.updateVelocityLimit(vel_limit);  // also caps P_angle output

  motor_.loopFOC();                       // refresh shaft_angle; still disabled
  const float start = motor_.shaft_angle;
  motor_.target = start + travel_rad;

  enable();

  const uint32_t t0 = millis();
  bool arrived = false;
  while (millis() - t0 < timeout_ms) {
    motor_.loopFOC();
    motor_.move();
    if (fabsf(motor_.target - motor_.shaft_angle) < tolerance_rad &&
        fabsf(motor_.shaft_velocity) < 0.20f) {
      arrived = true;
      break;
    }
  }

  disable();

  // Back to the idle state so the main loop cannot re-energise: a nonzero
  // angle target is a position, not a request for torque.
  motor_.controller = MotionControlType::torque;
  motor_.target = 0;

  return arrived;
}
