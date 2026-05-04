/*
 * Standalone Sensor + Servo Test
 * ─────────────────────────────────────────────
 * HC-SR04:
 *   TRIG → Pin 9
 *   ECHO → Pin 10
 *
 * Servo Motor:
 *   Signal → Pin 6
 *   VCC    → 5V
 *   GND    → GND
 *
 * Behavior:
 *   distance ≤ 30cm → servo opens to 90°
 *   distance > 40cm → servo closes to 0°
 *
 * Serial output (9600 baud):
 *   "Distance: XX.XX cm"
 *   ">>> CAR DETECTED — Gate OPENING"
 *   ">>> Clear — Gate CLOSING"
 */

#include <Servo.h>

#define TRIG_PIN  9
#define ECHO_PIN  10
#define SERVO_PIN 6

#define THRESHOLD_OPEN  30   // cm — open gate when closer than this
#define THRESHOLD_CLOSE 40   // cm — close gate when farther than this
#define OPEN_ANGLE      90   // degrees
#define CLOSE_ANGLE     0    // degrees

Servo gateServo;
bool gateOpen = false;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  gateServo.attach(SERVO_PIN);
  gateServo.write(CLOSE_ANGLE);  // Start closed

  Serial.println("=== Sensor + Servo Test Ready ===");
  Serial.println("Servo pin: 6  |  Trigger: 9  |  Echo: 10");
  Serial.println("=================================");
}

void loop() {
  float dist = measureDistance();

  // Print distance
  Serial.print("Distance: ");
  Serial.print(dist);
  Serial.println(" cm");

  // Open gate when car detected
  if (dist > 0 && dist <= THRESHOLD_OPEN && !gateOpen) {
    gateOpen = true;
    gateServo.write(OPEN_ANGLE);
    Serial.println(">>> CAR DETECTED — Gate OPENING (90 deg)");
  }

  // Close gate when car is gone
  if (dist > THRESHOLD_CLOSE && gateOpen) {
    gateOpen = false;
    gateServo.write(CLOSE_ANGLE);
    Serial.println(">>> Clear — Gate CLOSING (0 deg)");
  }

  delay(300);  // Read every 300ms
}

// ─── Measure distance using HC-SR04 ───────────────────────────
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
