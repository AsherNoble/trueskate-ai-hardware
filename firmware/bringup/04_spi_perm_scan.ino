// BRINGUP ARCHIVE -- unchanged from ~/teensy. Bit-banged all 24 CS/CLK/MOSI/MISO permutations; found the one live mapping after the damaged JST plug was replaced.
// 04_spi_perm_scan.ino
//
// The four encoder signal wires are on pins 10..13 in an unknown
// arrangement. This tries all 24 assignments of {CSn, CLK, MOSI, MISO}
// and reports which, if any, produces a genuinely driven response.
//
// Bit-banged deliberately: the SPI peripheral is never begun, so it
// never claims pins 10..13 and every pin can take any role.
//
// VDD (3.3V) and GND are not touched by this sketch.

const uint8_t PINS[4] = {10, 11, 12, 13};

// ~10 kHz. Nothing here is timing-critical; slow is free.
const uint32_t HALF_PERIOD_US = 50;

// Command frames, parity already correct (bit 15 = even parity over 14:0).
const uint16_t CMD_ANGLE = 0xFFFF;  // read 0x3FFF
const uint16_t CMD_DIAG  = 0x7FFD;  // read 0x3FFD
const uint16_t CMD_NOP   = 0xC000;  // read 0x0000, used as the 2nd frame

struct Roles { uint8_t cs, clk, mosi, miso; };

// Even parity over the whole 16-bit word: XOR of all bits must be 0.
bool parityOk(uint16_t w) {
  uint8_t p = 0;
  while (w) { p ^= (w & 1); w >>= 1; }
  return p == 0;
}

void idleAllPins() {
  for (uint8_t i = 0; i < 4; i++) pinMode(PINS[i], INPUT);
}

// Mode 1 (CPOL=0, CPHA=1), MSB first. CLK idles low. The slave latches
// MOSI on the falling edge and drives MISO on the rising edge, so the
// master presents MOSI before the rising edge and samples MISO at the
// falling edge.
uint16_t transferFrame(const Roles &r, uint16_t out) {
  uint16_t in = 0;

  digitalWrite(r.cs, LOW);
  delayMicroseconds(2);              // >= 1us of CSn low before the first clock

  for (int8_t bit = 15; bit >= 0; bit--) {
    digitalWrite(r.mosi, (out >> bit) & 1);
    delayMicroseconds(1);            // settle before the edge

    digitalWrite(r.clk, HIGH);       // rising: slave presents its MISO bit
    delayMicroseconds(HALF_PERIOD_US);

    digitalWrite(r.clk, LOW);        // falling: slave latches MOSI
    in = (in << 1) | (digitalRead(r.miso) & 1);
    delayMicroseconds(HALF_PERIOD_US);
  }

  digitalWrite(r.cs, HIGH);
  delayMicroseconds(2);              // >= 1us of CSn high between frames
  return in;
}

// Pipelined: the command frame's answer arrives in the following frame.
uint16_t readRegister(const Roles &r, uint16_t cmd) {
  transferFrame(r, cmd);
  return transferFrame(r, CMD_NOP);
}

// pull is INPUT_PULLUP or INPUT_PULLDOWN, applied to the candidate MISO.
// A line the sensor really drives reads the same either way; a floating
// line just follows whichever resistor is attached.
void configure(const Roles &r, uint8_t pull) {
  idleAllPins();

  pinMode(r.cs, OUTPUT);
  digitalWrite(r.cs, HIGH);
  pinMode(r.clk, OUTPUT);
  digitalWrite(r.clk, LOW);          // CLK idles low
  pinMode(r.mosi, OUTPUT);
  digitalWrite(r.mosi, LOW);
  pinMode(r.miso, pull);

  delayMicroseconds(200);
}

void scanOnce() {
  const uint8_t order[24][4] = {
    {0,1,2,3},{0,1,3,2},{0,2,1,3},{0,2,3,1},{0,3,1,2},{0,3,2,1},
    {1,0,2,3},{1,0,3,2},{1,2,0,3},{1,2,3,0},{1,3,0,2},{1,3,2,0},
    {2,0,1,3},{2,0,3,1},{2,1,0,3},{2,1,3,0},{2,3,0,1},{2,3,1,0},
    {3,0,1,2},{3,0,2,1},{3,1,0,2},{3,1,2,0},{3,2,0,1},{3,2,1,0},
  };

  Serial.println();
  Serial.println("=== SPI permutation scan ===");
  Serial.println(" CS CLK MOSI MISO | ang_pu ang_pd  same | dia_pu dia_pd  same | par err OCF | angle");
  Serial.println("------------------+---------------------+---------------------+-------------+------");

  uint8_t hits = 0;

  for (uint8_t i = 0; i < 24; i++) {
    Roles r;
    r.cs   = PINS[order[i][0]];
    r.clk  = PINS[order[i][1]];
    r.mosi = PINS[order[i][2]];
    r.miso = PINS[order[i][3]];

    configure(r, INPUT_PULLUP);
    uint16_t angPu = readRegister(r, CMD_ANGLE);
    uint16_t diaPu = readRegister(r, CMD_DIAG);

    configure(r, INPUT_PULLDOWN);
    uint16_t angPd = readRegister(r, CMD_ANGLE);
    uint16_t diaPd = readRegister(r, CMD_DIAG);

    idleAllPins();

    bool angSame = (angPu == angPd);
    bool diaSame = (diaPu == diaPd);
    uint16_t angData = angPu & 0x3FFF;
    bool par   = parityOk(angPu);
    bool err   = angPu & 0x4000;
    bool ocf   = (diaPu & 0x0100) != 0;
    bool alive = angData != 0x0000 && angData != 0x3FFF;

    bool hit = angSame && diaSame && par && !err && alive && ocf;
    if (hit) hits++;

    Serial.printf(" %2u  %2u   %2u   %2u | 0x%04X 0x%04X  %-3s | 0x%04X 0x%04X  %-3s | %-3s %-3s %-3s | %5u%s\n",
                  r.cs, r.clk, r.mosi, r.miso,
                  angPu, angPd, angSame ? "yes" : "no",
                  diaPu, diaPd, diaSame ? "yes" : "no",
                  par ? "ok" : "BAD",
                  err ? "SET" : "ok",
                  ocf ? "ok" : "no",
                  angData,
                  hit ? "   <== HIT" : "");
  }

  Serial.println("------------------+---------------------+---------------------+-------------+------");
  Serial.printf("hits: %u\n", hits);
  if (hits == 0) {
    Serial.println("No assignment produced a driven, valid response.");
    Serial.println("Every candidate MISO either followed its pull resistor");
    Serial.println("or returned an all-zeros / all-ones word.");
  }
  Serial.println("Press 's' to scan again.");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  idleAllPins();

  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  Serial.println("AS5048A bit-banged SPI permutation scan");
  Serial.println("Hardware SPI is not initialised. Pins 10-13 only.");
  scanOnce();
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 's') scanOnce();
  }
}
