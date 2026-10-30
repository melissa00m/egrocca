/*
 * ShopDroid Low-Level Firmware: DC Motor Driver, Steering & Hardware E-Stop
 * Compatible with Arduino Uno, Nano, Mega, and ESP32.
 * Matches XOD patch: shopdroid-motor-controller
 *
 * Pin Connections:
 *   - Ultrasonic Sensor HC-SR04:
 *       TRIG: Pin D2
 *       ECHO: Pin D3
 *   - Left Motor (L298N H-Bridge):
 *       DIR:  Pin D4 (IN1/IN2)
 *       PWM:  Pin D5 (ENA)
 *   - Right Motor (L298N H-Bridge):
 *       PWM:  Pin D6 (ENB)
 *       DIR:  Pin D7 (IN3/IN4)
 */

#define PIN_TRIG 2
#define PIN_ECHO 3

#define PIN_MOTOR_L_DIR 4
#define PIN_MOTOR_L_PWM 5
#define PIN_MOTOR_R_PWM 6
#define PIN_MOTOR_R_DIR 7

// Safety threshold in meters (30 cm)
const float ESTOP_DISTANCE_METERS = 0.30f;

// Navigation command values (-1.0 to 1.0)
float v_linear = 0.5f;   // Default forward cruise
float w_angular = 0.0f;  // Default straight

void setup() {
  Serial.begin(115200);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  pinMode(PIN_MOTOR_L_DIR, OUTPUT);
  pinMode(PIN_MOTOR_L_PWM, OUTPUT);
  pinMode(PIN_MOTOR_R_DIR, OUTPUT);
  pinMode(PIN_MOTOR_R_PWM, OUTPUT);

  Serial.println(F("[FIRMWARE READY] ShopDroid Motor Controller Active."));
}

// Read ultrasonic distance in meters
float readDistanceMeters() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duration_us = pulseIn(PIN_ECHO, HIGH, 30000); // 30ms timeout (~5m)
  if (duration_us == 0) return 999.0f; // No echo -> clear path

  // Speed of sound: 340 m/s -> (duration * 0.00034) / 2
  return (float)duration_us * 0.00017f;
}

// Apply speed to individual DC motor (-1.0 to 1.0)
void setMotor(int dirPin, int pwmPin, float speed) {
  // Clamp speed to [-1.0, 1.0]
  if (speed > 1.0f) speed = 1.0f;
  if (speed < -1.0f) speed = -1.0f;

  bool forward = (speed >= 0.0f);
  int pwmVal = (int)(fabs(speed) * 255.0f);

  digitalWrite(dirPin, forward ? HIGH : LOW);
  analogWrite(pwmPin, pwmVal);
}

void loop() {
  // 1. Read incoming Serial command if available: e.g. "V:0.6,W:0.2\n"
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("V:")) {
      int commaIdx = cmd.indexOf(',');
      if (commaIdx > 0) {
        v_linear = cmd.substring(2, commaIdx).toFloat();
        int wIdx = cmd.indexOf("W:", commaIdx);
        if (wIdx > 0) {
          w_angular = cmd.substring(wIdx + 2).toFloat();
        }
      }
    }
  }

  // 2. Measure distance
  float distance = readDistanceMeters();

  // 3. Differential Steering Mixer:
  //    Left = V - W, Right = V + W
  float targetLeft = v_linear - w_angular;
  float targetRight = v_linear + w_angular;

  // 4. Hardware Safety E-Stop Override
  float finalLeft = 0.0f;
  float finalRight = 0.0f;

  if (distance < ESTOP_DISTANCE_METERS) {
    // E-STOP ACTIVATED! Force motors to 0
    finalLeft = 0.0f;
    finalRight = 0.0f;
    Serial.print(F("[E-STOP HAZARD] Distance: "));
    Serial.print(distance);
    Serial.println(F(" m -> MOTORS LOCKED!"));
  } else {
    // Safe: apply normal steering output
    finalLeft = targetLeft;
    finalRight = targetRight;
  }

  // 5. Output to physical H-Bridge drivers
  setMotor(PIN_MOTOR_L_DIR, PIN_MOTOR_L_PWM, finalLeft);
  setMotor(PIN_MOTOR_R_DIR, PIN_MOTOR_R_PWM, finalRight);

  delay(50); // 20 Hz loop rate
}
