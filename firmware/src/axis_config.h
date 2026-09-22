// Per-axis hardware description.
//
// One AxisConfig fully describes a finger axis, so adding the middle
// finger is a new constant plus one more Axis instance -- no changes to
// Axis itself. Only INDEX_AXIS is instantiated today.

#pragma once

#include <Arduino.h>

struct AxisConfig {
  const char* name;

  // BLDCDriver3PWM: IN1, IN2, IN3, EN
  uint8_t pin_in1;
  uint8_t pin_in2;
  uint8_t pin_in3;
  uint8_t pin_enable;

  // MagneticSensorSPI chip select. Stock AS5048_SPI config (SPI_MODE1,
  // 1 MHz) is correct -- verified in bringup/06_sensor_only.
  uint8_t pin_sensor_cs;

  int   pole_pairs;
  float phase_resistance;      // ohms

  float voltage_power_supply;  // V
  float driver_voltage_limit;  // V

  // In voltage torque mode this is the ONLY current cap: current_limit is
  // inert on that path. At phase_resistance ohms, stall current is
  // motor_voltage_limit / phase_resistance.
  float motor_voltage_limit;   // V
  float current_limit;         // A, used by the current-based torque modes
  float voltage_sensor_align;  // V
};

// GM3506, 24N/22P -> 11 pole pairs, ~5.6 ohm phase resistance.
// Pole-pair check passed at 11 during bring-up (genuine motor, not a clone).
constexpr AxisConfig INDEX_AXIS = {
  .name                 = "index",
  .pin_in1              = 4,
  .pin_in2              = 5,
  .pin_in3              = 6,
  .pin_enable           = 8,
  .pin_sensor_cs        = 10,
  .pole_pairs           = 11,
  .phase_resistance     = 5.6f,
  .voltage_power_supply = 12.0f,
  .driver_voltage_limit = 6.0f,
  .motor_voltage_limit  = 2.0f,
  .current_limit        = 0.3f,
  .voltage_sensor_align = 1.5f,
};
