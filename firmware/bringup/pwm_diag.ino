// BRINGUP ARCHIVE -- unchanged from ~/teensy. Proved Teensy 4.1 pins 4/5/6 can produce PWM at all, independent of SimpleFOC, with EN held low so nothing reaches the motor.
// pwm_diag.ino  --  DIAGNOSTIC ONLY, not part of the motor project.
//
// Purpose: determine whether Teensy 4.1 pins 4/5/6 can produce PWM at all,
// independent of SimpleFOC. No library, no motor control.
//
// SAFETY: pin 8 (SimpleFOCMini EN) is driven LOW and held there, so the
// DRV8313 outputs stay high-impedance for the duration of this test.
// Nothing can reach the motor even if the PSU is live.
//
// Expected at 8-bit resolution (255 = 100% of 3.3V), measured pin-to-GND
// with a DC voltmeter:
//    pin 4 ->  64/255 = 25%  -> ~0.83 V
//    pin 5 -> 128/255 = 50%  -> ~1.65 V
//    pin 6 -> 191/255 = 75%  -> ~2.48 V

const int PIN_A = 4;
const int PIN_B = 5;
const int PIN_C = 6;
const int PIN_EN = 8;

void setup() {
  // Hold the driver disabled before touching anything else.
  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);

  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) {}

  pinMode(PIN_A, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  pinMode(PIN_C, OUTPUT);

  // Same frequency SimpleFOC uses by default.
  analogWriteFrequency(PIN_A, 25000);
  analogWriteFrequency(PIN_B, 25000);
  analogWriteFrequency(PIN_C, 25000);

  analogWriteResolution(8);

  analogWrite(PIN_A, 64);   // 25%
  analogWrite(PIN_B, 128);  // 50%
  analogWrite(PIN_C, 191);  // 75%

  pinMode(LED_BUILTIN, OUTPUT);

  Serial.println();
  Serial.println("PWM DIAGNOSTIC RUNNING (SimpleFOC not involved)");
  Serial.println("EN (pin 8) held LOW - driver disabled, motor cannot be driven.");
  Serial.println("Measure pin-to-GND, DC volts. Expect:");
  Serial.println("  pin 4  ~0.83 V   (25%)");
  Serial.println("  pin 5  ~1.65 V   (50%)");
  Serial.println("  pin 6  ~2.48 V   (75%)");
  Serial.println("LED blinking = sketch alive.");
}

void loop() {
  // Heartbeat so we can tell it is running, and so EN stays asserted low.
  digitalWrite(PIN_EN, LOW);
  digitalWrite(LED_BUILTIN, (millis() / 500) % 2);
}
