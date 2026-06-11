#include <Servo.h>
#include <Arduino.h>

Servo steeringServo;
Servo throttleESC;

// Buffer to store the incoming CRSF packet (Max channels frame is 26 bytes)
uint8_t crsfBuffer[30];
uint8_t bufferIndex = 0;

unsigned long lastPacketTime = 0;

void parseCrsfChannels(uint8_t* payload);

void setup() {
  // Serial1 handles pins D0 (RX) and D1 (TX) on Nano R4
  Serial1.begin(420000);

  steeringServo.attach(9);   // Physical Pin D9 for Rudder
  throttleESC.attach(10);    // Physical Pin D10 for Motor ESC

  // Set initial neutral states
  steeringServo.writeMicroseconds(1500);
  throttleESC.writeMicroseconds(1500);
}



void loop() {
  // Read incoming bytes from the ELRS Receiver
  while (Serial1.available() > 0) {
    uint8_t b = Serial1.read();

    // Look for the CRSF frame header/sync byte (0xC8 = Flight Controller Address)
    if (bufferIndex == 0 && b != 0xC8) {
      continue; // Skip until we find the start of a packet
    }

    crsfBuffer[bufferIndex++] = b;

    // Once we have the length byte (index 1), make sure we don't overflow
    if (bufferIndex == 2 && (crsfBuffer[1] > 28 || crsfBuffer[1] < 2)) {
      bufferIndex = 0; // Invalid packet size structure, reset
    }

    // Packet complete condition: Sync (1 byte) + Length (1 byte) + Payload Length
    if (bufferIndex > 2 && bufferIndex == (crsfBuffer[1] + 2)) {
      
      // Check if it's an RC Channels Packet (Type 0x16)
      if (crsfBuffer[2] == 0x16) {
        parseCrsfChannels(&crsfBuffer[3]);
        lastPacketTime = millis();
      }
      
      bufferIndex = 0; // Reset for next packet
    }
  }

  // Failsafe: If no packets received for 500ms, stop the motor
  if (millis() - lastPacketTime > 500) {
    throttleESC.writeMicroseconds(1500); 
  }
}

// Unpacks the 11-bit CRSF channel data format
void parseCrsfChannels(uint8_t* payload) {
  // Extracting Channel 1 (Steering) and Channel 2 (Throttle) from 11-bit chunks
  uint16_t ch1_raw = ((payload[0])       | (payload[1] << 8)) & 0x07FF;
  uint16_t ch2_raw = ((payload[1] >> 3)  | (payload[2] << 5)) & 0x07FF;

  // 1. Map raw CRSF to standard 1000 - 2000 range first
  int steeringPWM = map(ch1_raw, 172, 1811, 1000, 2000);
  int throttlePWM = map(ch2_raw, 172, 1811, 1000, 2000);

  // 2. Safely constrain them to the standard boundary
  steeringPWM = constrain(steeringPWM, 1000, 2000);
  throttlePWM = constrain(throttlePWM, 1000, 2000);

  // 3. SCALE THE STEERING ONLY (Leaving center at 1500)
  // This stretches 1000->500, 1500->1500 (stays identical), and 2000->2500
  int wideSteeringPWM = map(steeringPWM, 1000, 2000, 500, 2500);

  // Send the adjusted signals to your hardware
  steeringServo.writeMicroseconds(wideSteeringPWM);
  throttleESC.writeMicroseconds(throttlePWM); // Keep throttle standard!
}