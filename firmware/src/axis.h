// One finger axis: motor, driver, sensor and the state machine around them.
//
// Behaviour is carried over unchanged from bringup/03_closed_loop.ino:
//   - nothing energised at boot; the motor is disabled in begin()
//   - initFOC() runs only on demand, because it moves the shaft and so
//     needs the bench PSU live
//   - loopFOC() is called explicitly (SimpleFOC 2.4 requires it)
//   - the driver is enabled only while a move actually needs it

#pragma once

#include <SimpleFOC.h>

#include "axis_config.h"

class Axis {
 public:
  explicit Axis(const AxisConfig& cfg);

  // Construct and initialise motor/driver/sensor. Leaves the motor
  // DISABLED. Safe to call with the PSU off. Returns false if the driver
  // or motor failed to initialise.
  bool begin();

  // Align the sensor and run the pole-pair check. MOVES THE SHAFT, so the
  // PSU must be on. Leaves the motor disabled with target 0 on success.
  bool initFOC();

  // Must be called every iteration once ready(). No-op before that: with
  // no alignment, commutation would run against an unknown offset.
  void update();

  void enable();
  void disable();

  bool ready() const { return foc_ready_; }
  bool enabled() const { return driver_enabled_; }
  const AxisConfig& config() const { return cfg_; }

  // Blocking closed-loop move of `travel` radians, capped at `rpm`.
  // Angle mode; returns true if it arrived inside `tolerance_rad` before
  // `timeout_ms`. Always ends disabled, back in torque mode, target 0.
  bool moveBy(float travel_rad, float rpm, uint32_t timeout_ms,
              float tolerance_rad = 0.02f);

  float targetGet() const { return motor_.target; }
  void  targetSet(float v) { motor_.target = v; }
  float shaftAngle() const { return motor_.shaft_angle; }
  float shaftVelocity() const { return motor_.shaft_velocity; }
  float voltageQ() const { return motor_.voltage.q; }
  float zeroElectricAngle() const { return motor_.zero_electric_angle; }
  int   sensorDirection() const { return (int)motor_.sensor_direction; }
  bool  poleCheckOk() const { return motor_.pp_check_result; }

  void setMotionMode(MotionControlType mode) { motor_.controller = mode; }
  MotionControlType motionMode() const { return motor_.controller; }

 private:
  AxisConfig          cfg_;
  BLDCMotor           motor_;
  BLDCDriver3PWM      driver_;
  MagneticSensorSPI   sensor_;

  bool foc_ready_ = false;
  bool driver_enabled_ = false;
};
