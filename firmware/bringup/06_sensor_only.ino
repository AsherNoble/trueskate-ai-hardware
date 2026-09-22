// BRINGUP ARCHIVE -- unchanged from ~/teensy. Proved mode 1 still reads true under a single SPI.begin() with SimpleFOC's own MagneticSensorSPI -- stock AS5048_SPI needs no custom config.
// 06_sensor_only.ino
//
// Does mode 1 still read true when the SPI peripheral is started once
// and never torn down? 05 proved mode 1 correct, but it called
// SPI.end() / pinMode() / SPI.begin() on every iteration for its
// bit-bang leg. Sketch 01 used the same mode 1 with a single begin()
// and read one bit late.
//
// This is the configuration phase 2 will actually run in: SimpleFOC's
// own sensor class, stock AS5048_SPI config (already SPI_MODE1 @ 1MHz),
// one init(), no bit-banging.
//
// No driver, no motor. Wiring: CS 10, CLK 13, MOSI 11, MISO 12.

#include <SimpleFOC.h>

MagneticSensorSPI sensor(AS5048_SPI, 10);

uint32_t lastPrint = 0;

void setup() {
  Serial.begin(115200);

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  SimpleFOCDebug::enable(&Serial);

  Serial.println("SimpleFOC MagneticSensorSPI, stock AS5048_SPI config");
  Serial.println("SPI_MODE1 @ 1MHz, single SPI.begin(), no bit-bang");

  sensor.init();

  Serial.println("sensor.init() returned");
  Serial.println();
}

void loop() {
  sensor.update();

  if (millis() - lastPrint >= 100) {
    lastPrint = millis();

    float mech = sensor.getMechanicalAngle();      // 0..2PI, wraps
    float full = sensor.getAngle();                // accumulates turns
    float deg  = mech * 180.0f / PI;
    uint16_t raw = (uint16_t)(mech / _2PI * 16384.0f);

    Serial.printf("raw %5u   %7.2f deg   total %8.2f deg\n",
                  raw, deg, full * 180.0f / PI);
  }
}
