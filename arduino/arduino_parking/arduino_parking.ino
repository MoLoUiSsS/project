/*
 * Smart Parking System — Arduino Sketch (FINAL)
 * ─────────────────────────────────────────────
 * Wiring:
 *   HC-SR04:
 *     VCC  → 5V       GND  → GND
 *     TRIG → Pin 9    ECHO → Pin 10
 *
 *   Servo Motor (Gate):
 *     Signal → Pin 6    VCC → 5V    GND → GND
 *
 * Serial Protocol (9600 baud):
 *   Arduino → PC:   "DIST:<cm>"          every 300ms
 *   Arduino → PC:   "CAR_DETECTED"       when distance < 30cm
 *   Arduino → PC:   "GATE_OPENED"        after opening
 *   Arduino → PC:   "GATE_CLOSED"        after closing
 *   Arduino → PC:   "PARKING_SYSTEM_READY" on boot
 *
 *   PC → Arduino:   "GATE:OPEN"          rotate servo to 90°
 *   PC → Arduino:   "GATE:CLOSE"         rotate servo to 0°
 */

#include <Servo.h>

// ─── Pin definitions ────────────────────────────────────────
#define TRIG_PIN  9
#define ECHO_PIN  10
#define SERVO_PIN 6

// ─── Settings ───────────────────────────────────────────────
#define DETECTION_DISTANCE  30    // cm — trigger when closer
#define CLEAR_DISTANCE      40    // cm — reset when farther
#define GATE_OPEN_ANGLE     90    // degrees — open position
#define GATE_CLOSE_ANGLE    0     // degrees — closed position
#define MEASURE_INTERVAL    300   // ms between readings
#define GATE_AUTO_CLOSE     10000 // ms — auto-close after 10s
#define DEBOUNCE_DELAY      5000  // ms — min time between triggers

// ─── Globals ────────────────────────────────────────────────
Servo gateServo;
bool  gateOpen      = false;
bool  carDetected   = false;

unsigned long lastMeasure   = 0;
unsigned long gateOpenTime  = 0;
unsigned long debounceTime  = 0;

String inputBuffer = "";

// ─── Setup ──────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  gateServo.attach(SERVO_PIN);
  gateServo.write(GATE_CLOSE_ANGLE);   // Start closed

  delay(500);
  Serial.println("PARKING_SYSTEM_READY");
}

// ─── Main Loop ──────────────────────────────────────────────
void loop() {

  // 1. Read commands from Python (GATE:OPEN / GATE:CLOSE)
  readSerialCommands();

  // 2. Measure distance every MEASURE_INTERVAL ms
  unsigned long now = millis();
  if (now - lastMeasure >= MEASURE_INTERVAL) {
    lastMeasure = now;

    float dist = measureDistance();

    // Send distance to Python (format: "DIST:24")
    if (dist > 0) {
      Serial.print("DIST:");
      Serial.println((int)dist);
    }

    // Car approaching → notify Python ONLY
    // Gate opens ONLY after Python verifies plate in DB
    if (dist > 0 && dist < DETECTION_DISTANCE
        && !carDetected
        && (now - debounceTime > DEBOUNCE_DELAY)) {

      carDetected  = true;
      debounceTime = now;
      Serial.println("CAR_DETECTED");
      // Do NOT call openGate() here — wait for Python GATE:OPEN command
    }

    // Car cleared
    if (dist > CLEAR_DISTANCE) {
      carDetected = false;
    }
  }

  // 3. Auto-close gate after timeout
  if (gateOpen && (millis() - gateOpenTime > GATE_AUTO_CLOSE)) {
    closeGate();
  }
}

// ─── Open Gate ──────────────────────────────────────────────
void openGate() {
  gateOpen     = true;
  gateOpenTime = millis();
  gateServo.write(GATE_OPEN_ANGLE);
  Serial.println("GATE_OPENED");
}

// ─── Close Gate ─────────────────────────────────────────────
void closeGate() {
  gateOpen = false;
  gateServo.write(GATE_CLOSE_ANGLE);
  Serial.println("GATE_CLOSED");
}

// ─── Read Serial Commands from Python ───────────────────────
void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      inputBuffer.trim();

      if (inputBuffer == "GATE:OPEN") {
        openGate();
      } else if (inputBuffer == "GATE:CLOSE") {
        closeGate();
      }

      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

// ─── Measure HC-SR04 Distance (cm) ──────────────────────────
float measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  if (duration == 0) return -1;

  return duration * 0.034 / 2.0;  // microseconds → cm
}
