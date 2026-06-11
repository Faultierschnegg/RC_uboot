#include <Arduino.h>
#line 1 "C:\\Users\\Niki\\VSCode\\RC_controller_elrs\\RC_controller_elrs.ino"
#include <AlfredoCRSF.h>

// Initialize the CRSF parser
AlfredoCRSF crsf;

void setup() {
  // 1. Initialize the USB connection to your PC for debugging
  Serial.begin(115200); 

  // 2. Initialize Hardware Serial1 connected to ELRS Receiver (Pins D0/D1)
  // CRSF/ELRS strictly operates at 420000 baud
  Serial1.begin(420000); 

  // 3. Hand over the Serial1 port to the parsing engine
  crsf.begin(Serial1);

  Serial.println("Arduino Nano R4 ELRS Receiver Ready...");
}

void loop() {
  // Check the serial buffer for incoming packets from the receiver
  crsf.update();

  // Only run code if the receiver is actively bound and talking to the transmitter
  if (crsf.isLinkUp()) {
    
    // Read the Analog Joysticks (Channels 1 to 4)
    int steering = crsf.getChannel(1); // Left Stick X
    int rrl      = crsf.getChannel(2); // Right Stick X
    int throttle = crsf.getChannel(3); // Left Stick Y
    int rud      = crsf.getChannel(4); // Right Stick Y

    // Read the mapped Button States (Channels 5 to 12)
    // These will read roughly 1000 (Not Pressed) or 2000 (Pressed)
    int btn_A   = crsf.getChannel(5);
    int btn_B   = crsf.getChannel(6);
    int btn_X   = crsf.getChannel(7);
    int btn_Y   = crsf.getChannel(8);
    int btn_LB  = crsf.getChannel(9);
    int btn_RB  = crsf.getChannel(10);
    int btn_Min = crsf.getChannel(11);
    int btn_Crs = crsf.getChannel(12);

    // --- Print Data to PC Serial Monitor ---
    Serial.print("STEER: "); Serial.print(steering);
    Serial.print(" | THROTTLE: "); Serial.print(throttle);
    
    // Check digital threshold to see if button A is pressed
    Serial.print(" | A-BTN: ");
    if (btn_A > 1500) Serial.print("PRESSED");
    else              Serial.print("RELEASED");
    
    Serial.println(); // New line

  } else {
    // Keeps you informed if the transmitter link drops or isn't powered on
    Serial.println("No link to ELRS Receiver. Check transmitter power...");
    delay(500); 
  }

  // A tiny 10ms pacing delay matches the ultra-fast update intervals of ELRS
  delay(10); 
}


