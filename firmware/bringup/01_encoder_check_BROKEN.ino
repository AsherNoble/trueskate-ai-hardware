// BRINGUP ARCHIVE -- unchanged from ~/teensy. BROKEN: proved nothing about the encoder -- every word read one bit shifted (a quarter turn read as ~180 deg). Superseded by 06_sensor_only.
// 01_encoder_check.ino
//
// AS5048A over raw SPI. No SimpleFOC, deliberately — this isolates
// wiring and SPI faults from library configuration.
//
// Runs on USB power alone. Motor disconnected, Mini unpowered.
//
// Wiring (Teensy 4.1):
//   13 SCK  -> CLK
//   12 MISO -> DO
//   11 MOSI -> DI
//   10 CS   -> CSn
//   3.3V    -> VDD      (never 5V)
//   GND     -> GND

#include <SPI.h>

const uint8_t CS_PIN = 10;

// 1 MHz, not 10. Breadboard wiring does not deserve the benefit of the doubt.
SPISettings as5048(1000000, MSBFIRST, SPI_MODE1);

const uint16_t REG_NOP    = 0x0000;
const uint16_t REG_ERRFLG = 0x0001;
const uint16_t REG_DIAG   = 0x3FFD;  // AGC + diagnostics
const uint16_t REG_MAG    = 0x3FFE;  // CORDIC magnitude
const uint16_t REG_ANGLE  = 0x3FFF;

uint32_t frames = 0, parityErrors = 0, errorFlags = 0;
uint16_t angleMin = 0x3FFF, angleMax = 0;
uint32_t lastPrint = 0;

// Bit 15 is even parity over bits 14:0.
uint16_t withParity(uint16_t v) {
  uint16_t t = v;
  uint8_t p = 0;
  while (t) { p ^= (t & 1); t >>= 1; }
  return p ? (v | 0x8000) : v;
}

uint16_t transfer16(uint16_t out) {
  SPI.beginTransaction(as5048);
  digitalWrite(CS_PIN, LOW);
  delayMicroseconds(1);
  uint16_t in = SPI.transfer16(out);
  delayMicroseconds(1);
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();
  delayMicroseconds(2);
  return in;
}

// The AS5048A is pipelined: a read command returns the PREVIOUS frame's
// data. So issue the command, then a NOP, and keep the second response.
uint16_t readRegister(uint16_t addr) {
  uint16_t cmd = withParity(0x4000 | (addr & 0x3FFF));
  transfer16(cmd);
  uint16_t resp = transfer16(withParity(0x4000 | REG_NOP));

  frames++;

  uint16_t body = resp & 0x7FFF;
  uint8_t p = 0;
  uint16_t t = body;
  while (t) { p ^= (t & 1); t >>= 1; }
  if (p != ((resp >> 15) & 1)) parityErrors++;

  if (resp & 0x4000) {
    errorFlags++;
    transfer16(withParity(0x4000 | REG_ERRFLG));  // reading it clears it
    transfer16(withParity(0x4000 | REG_NOP));
  }

  return resp & 0x3FFF;
}

void reportDiagnostics() {
  uint16_t d = readRegister(REG_DIAG);
  uint8_t agc  = d & 0xFF;
  bool ocf     = d & (1 << 8);   // offset compensation finished — want true
  bool cof     = d & (1 << 9);   // CORDIC overflow — want false
  bool compLow = d & (1 << 10);  // field too strong, magnet too close
  bool compHi  = d & (1 << 11);  // field too weak, magnet too far or absent

  Serial.println();
  Serial.println("--- diagnostics ---");
  Serial.printf("  AGC        %u  (0 = strong field, 255 = weak)\n", agc);
  Serial.printf("  OCF        %s\n", ocf ? "ok" : "NOT FINISHED");
  Serial.printf("  COF        %s\n", cof ? "OVERFLOW" : "ok");
  Serial.printf("  COMP low   %s\n", compLow ? "FIELD TOO STRONG" : "ok");
  Serial.printf("  COMP high  %s\n", compHi ? "FIELD TOO WEAK / NO MAGNET" : "ok");
  Serial.printf("  magnitude  %u\n", readRegister(REG_MAG));

  if (d == 0x0000 || d == 0x3FFF) {
    Serial.println("  >> Register reads all-zeros or all-ones.");
    Serial.println("     That is a wiring or power fault, not a magnet problem.");
    Serial.println("     Check VDD is 3.3V, CSn is on pin 10, DO is on pin 12.");
  } else if (compHi && agc > 240) {
    Serial.println("  >> No magnet in range. SPI itself is working.");
  } else if (ocf && !cof && !compHi && !compLow) {
    Serial.println("  >> Sensor healthy. Angle readings below are trustworthy.");
  }
  Serial.println("-------------------");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  SPI.begin();

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  Serial.println("AS5048A raw SPI check");
  delay(50);
  reportDiagnostics();
}

void loop() {
  uint16_t raw = readRegister(REG_ANGLE);

  if (raw < angleMin) angleMin = raw;
  if (raw > angleMax) angleMax = raw;

  if (millis() - lastPrint >= 100) {
    lastPrint = millis();
    float deg = raw * 360.0f / 16384.0f;
    Serial.printf("raw %5u   %7.2f deg   span %u   parity_err %lu   err_flag %lu\n",
                  raw, deg, angleMax - angleMin, parityErrors, errorFlags);
  }

  // 'd' re-runs diagnostics, 'r' resets the span tracker.
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'd') reportDiagnostics();
    if (c == 'r') { angleMin = 0x3FFF; angleMax = 0; parityErrors = 0; errorFlags = 0; }
  }

  delay(5);
}
