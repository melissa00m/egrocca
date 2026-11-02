
/*
 * ==============================================================================
 * Rural Delivery Droid - Electronic Compartment Lock & Anti-Tamper Controller
 * Matches XOD Patches: main.xodp, rfid-validator.xodp, solenoid-controller.xodp, tamper-detector.xodp
 * 
 * Hardware Requirements:
 *  - Microcontroller: Arduino Uno / Nano / Mega or ESP32
 *  - RFID Reader: MFRC522 (13.56 MHz RFID/NFC) via SPI
 *  - Solenoid Lock: 12V DC Solenoid Door Bolt (via 5V Optocoupled Relay or IRLZ44N MOSFET)
 *  - Door Sensor: Magnetic Reed Switch (Normally Closed when door shut)
 *  - Status LEDs: Green (Access Granted), Red (Access Denied / Tamper Alert)
 *  - Audio: Piezo Buzzer
 *  - Interface to Droid SBC: Digital Pin D3 (Tamper Interrupt line to Raspberry Pi / Node-RED)
 * 
 * Pinout:
 *  - MFRC522 SDA (SS): Pin 10
 *  - MFRC522 SCK     : Pin 13
 *  - MFRC522 MOSI    : Pin 11
 *  - MFRC522 MISO    : Pin 12
 *  - MFRC522 RST     : Pin 9
 *  - Reed Switch     : Pin 2 (INPUT_PULLUP)
 *  - Tamper Alert Out: Pin 3 (OUTPUT to SBC / Node-RED GPIO)
 *  - Piezo Buzzer    : Pin 4
 *  - Green LED       : Pin 5
 *  - Red LED         : Pin 6
 *  - Relay Solenoid  : Pin 7 (ACTIVE HIGH)
 * ==============================================================================
 */

#include <SPI.h>
#include <MFRC522.h>

// Pin Definitions
#define PIN_REED_SWITCH     2
#define PIN_TAMPER_ALERT    3
#define PIN_BUZZER          4
#define PIN_LED_GREEN       5
#define PIN_LED_RED         6
#define PIN_RELAY_SOLENOID  7
#define PIN_RFID_RST        9
#define PIN_RFID_SS         10

// Timing & Configuration Constants
const unsigned long SOLENOID_MAX_HOLD_MS = 12000; // 12 seconds max energize time (coil protection)
const unsigned long TAMPER_RESET_WINDOW_MS = 30000; // 30 seconds sliding window for failed scans
const int MAX_FAILED_ATTEMPTS = 3;

// Authorized Customer Delivery Key (Can be updated dynamically over Serial by SBC/Node-RED)
String currentAuthorizedUID = "E2 4B 89 1A";

// State Machine Variables
bool isUnlocked = false;
bool tamperAlertActive = false;
unsigned long unlockTimestamp = 0;
int failedScanCount = 0;
unsigned long lastFailedScanTime = 0;

MFRC522 mfrc522(PIN_RFID_SS, PIN_RFID_RST);

void playToneSuccess() {
  tone(PIN_BUZZER, 1800, 100);
  delay(120);
  tone(PIN_BUZZER, 2400, 200);
}

void playToneDenied() {
  tone(PIN_BUZZER, 400, 250);
  delay(150);
  tone(PIN_BUZZER, 300, 400);
}

void playToneAlarm() {
  for (int i = 0; i < 3; i++) {
    tone(PIN_BUZZER, 3000, 80);
    delay(100);
    tone(PIN_BUZZER, 1200, 80);
    delay(100);
  }
}

void unlockCompartment() {
  isUnlocked = true;
  unlockTimestamp = millis();
  digitalWrite(PIN_RELAY_SOLENOID, HIGH); // Energize solenoid
  digitalWrite(PIN_LED_GREEN, HIGH);
  digitalWrite(PIN_LED_RED, LOW);
  playToneSuccess();
  Serial.println(F("[LOCK_SYSTEM] STATUS: UNLOCKED | Solenoid energized"));
}

void lockCompartment() {
  isUnlocked = false;
  digitalWrite(PIN_RELAY_SOLENOID, LOW); // De-energize solenoid (spring returns bolt)
  digitalWrite(PIN_LED_GREEN, LOW);
  Serial.println(F("[LOCK_SYSTEM] STATUS: LOCKED | Compartment secured"));
}

void triggerTamperAlarm(const char* reason) {
  tamperAlertActive = true;
  digitalWrite(PIN_TAMPER_ALERT, HIGH); // Signal Companion Computer (SBC)
  digitalWrite(PIN_LED_RED, HIGH);
  playToneAlarm();
  
  Serial.print(F("[SECURITY_ALERT] TAMPER_DETECTED: "));
  Serial.println(reason);
}

void clearTamperAlarm() {
  tamperAlertActive = false;
  digitalWrite(PIN_TAMPER_ALERT, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  failedScanCount = 0;
  Serial.println(F("[SECURITY_ALERT] Tamper alarm cleared."));
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000); // Wait for serial console on USB

  // Initialize GPIOs
  pinMode(PIN_REED_SWITCH, INPUT_PULLUP);
  pinMode(PIN_TAMPER_ALERT, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_RELAY_SOLENOID, OUTPUT);

  // Set initial safe states (Locked & Secure)
  digitalWrite(PIN_RELAY_SOLENOID, LOW);
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_TAMPER_ALERT, LOW);

  // Initialize SPI & RFID Reader
  SPI.begin();
  mfrc522.PCD_Init();
  delay(10);
  mfrc522.PCD_DumpVersionToSerial();

  Serial.println(F("=================================================="));
  Serial.println(F(" Rural Delivery Droid - Compartment Lock Controller "));
  Serial.print(F(" Active Delivery Customer UID: "));
  Serial.println(currentAuthorizedUID);
  Serial.println(F("=================================================="));
}

void loop() {
  unsigned long now = millis();

  // 1. Check for Dynamic Customer Key Updates from Droid Flight Computer (Node-RED/SBC)
  // Format: "AUTH:<NEW_UID>" (e.g., "AUTH:A1 B2 C3 D4")
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("AUTH:")) {
      currentAuthorizedUID = cmd.substring(5);
      currentAuthorizedUID.trim();
      currentAuthorizedUID.toUpperCase();
      Serial.print(F("[LOCK_SYSTEM] New Authorized UID configured: "));
      Serial.println(currentAuthorizedUID);
      clearTamperAlarm();
    } else if (cmd == "FORCE_LOCK") {
      lockCompartment();
    } else if (cmd == "REMOTE_UNLOCK") {
      unlockCompartment();
    }
  }

  // 2. Door Reed Switch & Physical Pry Tamper Detection
  // Reed switch pin is LOW when door is firmly closed against magnetic strike
  bool isDoorOpen = (digitalRead(PIN_REED_SWITCH) == HIGH);

  // If door is opened while the system is in LOCKED state -> Physical pry/crowbar attack!
  if (!isUnlocked && isDoorOpen && !tamperAlertActive) {
    triggerTamperAlarm("COMPARTMENT_DOOR_PRIED_OPEN_WHILE_LOCKED");
  }

  // 3. Solenoid Failsafe Auto-Lock Management
  if (isUnlocked) {
    // If door was opened and has now been closed, relock immediately
    // Or if max hold time elapsed, force relock to protect solenoid from overheating
    if (now - unlockTimestamp >= SOLENOID_MAX_HOLD_MS) {
      Serial.println(F("[LOCK_SYSTEM] Failsafe timeout reached. Relocking..."));
      lockCompartment();
    }
  }

  // 4. Sliding Window Reset for Failed Scans
  if (failedScanCount > 0 && (now - lastFailedScanTime > TAMPER_RESET_WINDOW_MS)) {
    failedScanCount = 0;
  }

  // 5. Poll RFID/NFC Reader
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Extract UID string
  String scannedUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) scannedUID += "0";
    scannedUID += String(mfrc522.uid.uidByte[i], HEX);
    if (i < mfrc522.uid.size - 1) scannedUID += " ";
  }
  scannedUID.toUpperCase();

  Serial.print(F("[RFID_SCAN] Scanned Card UID: "));
  Serial.println(scannedUID);

  // Validate Scanned UID against Authorized Token
  if (scannedUID == currentAuthorizedUID) {
    Serial.println(F("[AUTH_SUCCESS] Customer UID Validated! Opening compartment..."));
    failedScanCount = 0;
    if (tamperAlertActive) clearTamperAlarm();
    unlockCompartment();
  } else {
    failedScanCount++;
    lastFailedScanTime = now;
    digitalWrite(PIN_LED_RED, HIGH);
    playToneDenied();
    delay(200);
    digitalWrite(PIN_LED_RED, LOW);

    Serial.print(F("[AUTH_FAILED] Invalid UID! Failed attempts: "));
    Serial.print(failedScanCount);
    Serial.print(F("/"));
    Serial.println(MAX_FAILED_ATTEMPTS);

    if (failedScanCount >= MAX_FAILED_ATTEMPTS) {
      triggerTamperAlarm("MULTIPLE_UNAUTHORIZED_RFID_SCANS");
    }
  }

  // Halt PICC and stop crypto
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(500); // Debounce card presence
}

