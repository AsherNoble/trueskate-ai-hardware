// DRV8871 + Chihai CHR-RK520: encoder-based one-revolution test.
// Wiring: IN1=D9, IN2=D10, encoder A=D2, encoder B=D3.

const uint8_t IN1_PIN = 9;
const uint8_t IN2_PIN = 10;
const uint8_t ENC_A_PIN = 2;
const uint8_t ENC_B_PIN = 3;

// The documented encoder is 11 PPR. Counting both A transitions gives 22.
const long COUNTS_PER_REV = 22;
const long BRAKE_START_COUNT = 20;
const uint8_t RUN_PWM = 100;
const unsigned long TIMEOUT_MS = 5000;
const unsigned long BRAKE_MS = 60;
const unsigned long CALIBRATION_MS = 2000;

volatile long encoderCount = 0;
bool manualCalibrationActive = false;

void encoderAChanged() {
  // Forward motion in the current wiring produces negative counts.
  encoderCount += digitalRead(ENC_B_PIN) ? -1 : 1;
}

long readEncoderCount() {
  noInterrupts();
  long result = encoderCount;
  interrupts();
  return result;
}

void coast() {
  analogWrite(IN1_PIN, 0);
  analogWrite(IN2_PIN, 0);
}

void forward(uint8_t pwm) {
  analogWrite(IN2_PIN, 0);
  analogWrite(IN1_PIN, pwm);
}

void brake() {
  // DRV8871: both inputs high applies active braking.
  analogWrite(IN1_PIN, 255);
  analogWrite(IN2_PIN, 255);
}

void runOneRevolution() {
  coast();
  delay(100);

  noInterrupts();
  encoderCount = 0;
  interrupts();

  Serial.println(F("RUNNING: one revolution"));
  unsigned long start = millis();
  while (abs(readEncoderCount()) < BRAKE_START_COUNT &&
         millis() - start < TIMEOUT_MS) {
    long progress = abs(readEncoderCount());
    // Slow down before the target to reduce mechanical overshoot.
    uint8_t pwm = progress >= BRAKE_START_COUNT - 6 ? 45
                  : progress >= BRAKE_START_COUNT - 12 ? 70
                  : RUN_PWM;
    forward(pwm);
  }

  brake();
  delay(BRAKE_MS);
  coast();

  long finalCount = readEncoderCount();
  Serial.print(F("Final encoder count: "));
  Serial.println(finalCount);
  Serial.print(F("Elapsed ms: "));
  Serial.println(millis() - start);
  Serial.println(F("DONE: motor stopped; send g to repeat"));
}

void runCalibration() {
  coast();
  delay(100);

  noInterrupts();
  encoderCount = 0;
  interrupts();

  Serial.println(F("RUNNING: 2-second calibration"));
  unsigned long start = millis();
  while (millis() - start < CALIBRATION_MS) {
    forward(RUN_PWM);
  }
  brake();
  delay(BRAKE_MS);
  coast();

  Serial.print(F("Calibration encoder count: "));
  Serial.println(readEncoderCount());
  Serial.println(F("DONE: motor stopped; send c to repeat"));
}

void startManualCalibration() {
  coast();
  noInterrupts();
  encoderCount = 0;
  interrupts();
  manualCalibrationActive = true;
  Serial.println(F("MANUAL: rotate the marked target shaft one full turn, then send x"));
}

void finishManualCalibration() {
  if (!manualCalibrationActive) {
    return;
  }
  manualCalibrationActive = false;
  coast();
  Serial.print(F("Manual one-turn count: "));
  Serial.println(readEncoderCount());
  Serial.println(F("DONE: motor stopped; send m to repeat"));
}

void setup() {
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  coast();

  pinMode(ENC_A_PIN, INPUT);
  pinMode(ENC_B_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PIN), encoderAChanged, CHANGE);

  Serial.begin(115200);
  delay(500);
  Serial.println(F("READY: send c for calibration or g for one revolution"));
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'm') {
      startManualCalibration();
    } else if (command == 'x') {
      finishManualCalibration();
    } else if (!manualCalibrationActive && command == 'g') {
      runOneRevolution();
    } else if (!manualCalibrationActive && command == 'c') {
      runCalibration();
    }
  }
}
