// BRINGUP ARCHIVE -- unchanged from ~/teensy. Proved SPI_MODE1 is the only correct hardware-SPI mode, checked against a bit-banged reference at two shaft positions.
// 05_spi_mode_sweep.ino
//
// Sketch 01 reads the AS5048A one bit late through the hardware SPI
// peripheral: a quarter turn reads as ~180 deg, jitter doubles, and
// parity fails on every frame. The bit-banged reader in 04 is correct.
//
// This sweeps SPI_MODE0..3 and, for each, compares a hardware read
// against a bit-banged read taken moments later at the same shaft
// position. The bit-bang is the reference.
//
// Wiring is fixed and correct:
//   CS 10, CLK 13, MOSI 11, MISO 12, VDD 3.3V, GND.

#include <SPI.h>

const uint8_t PIN_CS   = 10;
const uint8_t PIN_CLK  = 13;
const uint8_t PIN_MOSI = 11;
const uint8_t PIN_MISO = 12;

const uint32_t SPI_HZ = 1000000;

// Bit-bang half period. ~10 kHz, same as 04.
const uint32_t HALF_PERIOD_US = 50;

// Command frames, parity already correct in bit 15.
const uint16_t CMD_ANGLE  = 0xFFFF;  // read 0x3FFF
const uint16_t CMD_ERRFLG = 0x4001;  // read 0x0001 — reading it clears it
const uint16_t CMD_NOP    = 0xC000;  // read 0x0000, used as the 2nd frame

const uint8_t MODES[4] = {SPI_MODE0, SPI_MODE1, SPI_MODE2, SPI_MODE3};

// Even parity over the whole 16-bit word: XOR of all bits must be 0.
bool parityOk(uint16_t w) {
  uint8_t p = 0;
  while (w) { p ^= (w & 1); w >>= 1; }
  return p == 0;
}

// ---------- hardware SPI ----------

uint16_t hwFrame(uint16_t out, uint8_t mode) {
  SPISettings s(SPI_HZ, MSBFIRST, mode);
  SPI.beginTransaction(s);
  digitalWrite(PIN_CS, LOW);
  delayMicroseconds(1);
  uint16_t in = SPI.transfer16(out);
  delayMicroseconds(1);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
  delayMicroseconds(2);
  return in;
}

// Pipelined: the answer to a command arrives in the following frame.
uint16_t hwRead(uint16_t cmd, uint8_t mode) {
  hwFrame(cmd, mode);
  return hwFrame(CMD_NOP, mode);
}

// ---------- bit-banged SPI, the reference ----------

// Mode 1 by hand: CLK idles low, the slave latches MOSI on the falling
// edge and drives MISO on the rising edge, so present MOSI before the
// rising edge and sample MISO at the falling edge.
uint16_t bbFrame(uint16_t out) {
  uint16_t in = 0;

  digitalWrite(PIN_CS, LOW);
  delayMicroseconds(2);

  for (int8_t bit = 15; bit >= 0; bit--) {
    digitalWrite(PIN_MOSI, (out >> bit) & 1);
    delayMicroseconds(1);

    digitalWrite(PIN_CLK, HIGH);
    delayMicroseconds(HALF_PERIOD_US);

    digitalWrite(PIN_CLK, LOW);
    in = (in << 1) | (digitalRead(PIN_MISO) & 1);
    delayMicroseconds(HALF_PERIOD_US);
  }

  digitalWrite(PIN_CS, HIGH);
  delayMicroseconds(2);
  return in;
}

uint16_t bbRead(uint16_t cmd) {
  bbFrame(cmd);
  return bbFrame(CMD_NOP);
}

void bitBangPins() {
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_CS, HIGH);
  pinMode(PIN_CLK, OUTPUT);
  digitalWrite(PIN_CLK, LOW);
  pinMode(PIN_MOSI, OUTPUT);
  digitalWrite(PIN_MOSI, LOW);
  pinMode(PIN_MISO, INPUT);
  delayMicroseconds(200);
}

// ---------- sweep ----------

// 14-bit angles, compared the short way round the circle.
uint16_t angleDelta(uint16_t a, uint16_t b) {
  int32_t d = (int32_t)a - (int32_t)b;
  if (d < 0) d = -d;
  if (d > 8192) d = 16384 - d;
  return (uint16_t)d;
}

const uint16_t MATCH_TOLERANCE = 50;  // counts; covers jitter and the gap
                                      // between the two reads (~1.1 deg)

void sweepOnce() {
  Serial.println("mode | hw word  par err  hw ang | bb word  bb ang | delta match");
  Serial.println("-----+------------------------- +------------------+------------");

  for (uint8_t i = 0; i < 4; i++) {
    uint8_t mode = MODES[i];

    // --- hardware read ---
    SPI.begin();
    pinMode(PIN_CS, OUTPUT);
    digitalWrite(PIN_CS, HIGH);

    hwRead(CMD_ERRFLG, mode);          // clear anything latched by the
                                       // previous mode's bad framing
    uint16_t hw = hwRead(CMD_ANGLE, mode);

    SPI.end();

    // --- bit-banged read at the same position ---
    bitBangPins();
    bbRead(CMD_ERRFLG);                // clear again so the reference word
                                       // is not carrying the hw read's errors
    uint16_t bb = bbRead(CMD_ANGLE);

    uint16_t hwAng = hw & 0x3FFF;
    uint16_t bbAng = bb & 0x3FFF;
    uint16_t delta = angleDelta(hwAng, bbAng);
    bool match = delta <= MATCH_TOLERANCE;
    bool par   = parityOk(hw);
    bool err   = hw & 0x4000;

    bool good = par && !err && match;

    Serial.printf("  %u  | 0x%04X   %-3s %-3s  %5u | 0x%04X   %5u | %5u  %-3s%s\n",
                  i, hw, par ? "ok" : "BAD", err ? "SET" : "ok", hwAng,
                  bb, bbAng, delta, match ? "yes" : "no",
                  good ? "   <== GOOD" : "");
  }

  Serial.println();
}

void setup() {
  Serial.begin(115200);

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  Serial.println("AS5048A hardware-SPI mode sweep vs bit-banged reference");
  Serial.println("CS 10, CLK 13, MOSI 11, MISO 12. Rotate the shaft freely.");
  Serial.println();
}

void loop() {
  sweepOnce();
  delay(500);
}
