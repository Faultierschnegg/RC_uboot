import os
import time
import serial 
import sys
import serial.tools.list_ports
import pygame

print("running with elrs bridge")

# Initialize Pygame and the display subsystem
pygame.init()
pygame.joystick.init()

# CRITICAL: Create a tiny window so Windows processes joystick/keyboard events correctly
screen = pygame.display.set_mode((300, 100))
pygame.display.set_caption("ELRS Bridge")

num_controllers = pygame.joystick.get_count()
print(f"Total controllers detected by system: {num_controllers}")

for i in range(num_controllers):
    js = pygame.joystick.Joystick(i)
    js.init()
    print(f"Index {i}: {js.get_name()}")

def map_value(val, min_val, max_val):
    """Maps a -1.0 to 1.0 float to an RC pulse width (1000 to 2000)"""
    return int(1500 + (val * 500))

if pygame.joystick.get_count() == 0:
    print("No controller found. Plug in your 8BitDo controller and restart.")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()
print(f"Using controller: {controller.get_name()}\n")


def find_uart_adapter():
    """Scans system COM ports and returns ONLY physical USB-to-UART adapters"""
    ports = serial.tools.list_ports.comports()
    # Expanded keywords to catch generic Windows USB Serial descriptors
    physical_keywords = ["ch340", "cp210", "ftdi", "pl2303", "usb vid", "usb serial", "silicon labs"]
    
    for port in ports:
        dev = port.device
        desc = port.description.lower()
        hwid = port.hwid.lower()
        
        if "bluetooth" in desc or "bthenum" in hwid or "bth" in hwid:
            continue
            
        port_info = f"{desc} {hwid}"
        for keyword in physical_keywords:
            if keyword in port_info:
                print(f"--> Found Physical USB UART Adapter: {dev} ({port.description})")
                return dev
                
    for port in ports:
        desc = port.description.lower()
        hwid = port.hwid.lower()
        if "bluetooth" in desc or "bthenum" in hwid or "bth" in hwid:
            continue
        print(f"--> Fallback: Selecting non-Bluetooth port: {port.device} ({port.description})")
        return port.device
        
    return None

SERIAL_PORT = "COM5"
BAUD_RATE = 416666  # Must match ELRS receiver settings

if not SERIAL_PORT:
    print("Error: No active COM ports detected. Is your UART adapter plugged into the laptop?")
    exit()

try:
    # ADDED TIMEOUTS: Stops Python from freezing indefinitely if COM3 hangs
    arduino = serial.Serial(
        port=SERIAL_PORT, 
        baudrate=BAUD_RATE, 
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0,             # Do not block waiting for data
        write_timeout=None     # Infinite timeout for writing (keeps 50Hz stable)
    )
    print(f"Connected to Transmitter on {SERIAL_PORT}")
except Exception as e:
    print(f"Could not open serial port {SERIAL_PORT}: {e}")
    exit()

def crsf_crc8(data):
    """Calculates the unique CRC8 checksum required for CRSF packets"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0xD5
            else:
                crc <<= 1
            crc &= 0xFF
    return crc

def pack_crsf_channels(channels16):
    """Packs 16 channels (values 1000-2000) into CRSF 11-bit format"""
    payload = bytearray(22)
    bit_buffer = 0
    bit_count = 0
    byte_index = 0
    
    for ch in channels16:
        crsf_val = int((ch - 880) * 1.6)
        crsf_val = max(172, min(1811, crsf_val))
        
        bit_buffer |= (crsf_val << bit_count)
        bit_count += 11
        while bit_count >= 8:
            payload[byte_index] = bit_buffer & 0xFF
            bit_buffer >>= 8
            bit_count -= 8
            byte_index += 1
            
    frame = bytearray()
    frame.append(0xC8)       
    frame.append(24)         
    frame.append(0x16)       
    frame.extend(payload)
    
    crc = crsf_crc8(frame[2:])
    frame.append(crc)
    
    return frame

print("Bridge loop running.")
print("CLICK ON THE BLACK PYGAME WINDOW, then press 'ESC' to exit safely.")

print_counter = 0
running = True

try:
    while running:
        # Keep window updated and handle window closing events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Allow pressing the Escape key to close out cleanly
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            print("\nEscape pressed. Exiting...")
            running = False
        
        # 1. READ STICKS
        steering_axis = controller.get_axis(0)
        throttle_axis = controller.get_axis(1)
        rud_axis = controller.get_axis(4)
        rrl_axis = controller.get_axis(3)

        throttle = map_value(-throttle_axis, -1.0, 1.0)
        steering = map_value(steering_axis, -1.0, 1.0)
        rud = map_value(-rud_axis, -1.0, 1.0)
        rrl = map_value(rrl_axis, -1.0, 1.0)

        # 2. READ BUTTONS
        a = controller.get_button(0) 
        b = controller.get_button(1)
        x = controller.get_button(3)
        y = controller.get_button(4)
        lb = controller.get_button(6)
        rb = controller.get_button(7)
        l4 = controller.get_button(2)
        r4 = controller.get_button(5)
        minus = controller.get_button(10)
        cross = controller.get_button(11)
        lstick = controller.get_button(13)
        rstick = controller.get_button(14)
        lt = controller.get_button(8)
        rt = controller.get_button(9)

        dpad_x, dpad_y = controller.get_hat(0) 
        
        # 3. MAPPING CHANNELS
        channels = [1500] * 16
        channels[0] = steering
        channels[1] = throttle
        channels[2] = rud
        channels[3] = rrl

        xyba_ch5 = (a<<0)|(b<<1)|(x<<2)|(y<<3)
        channels[4] = 1000 + (xyba_ch5*60)
        channels[5] = 2000 if lb == 1 else 1000
        channels[6] = 2000 if rb == 1 else 1000
        channels[7] = 2000 if l4 == 1 else 1000
        channels[8] = 2000 if r4 == 1 else 1000
        channels[9] = 2000 if lstick == 1 else 1000
        channels[10] = 2000 if rstick == 1 else 1000
        channels[11] = 2000 if lt == 1 else 1000
        channels[12] = 2000 if rt == 1 else 1000
        channels[13] = 2000 if minus == 1 else 1000
        channels[14] = 2000 if cross == 1 else 1000

        dp_up = 1 if dpad_y == 1 else 0
        dp_down = 1 if dpad_y == -1 else 0
        dp_left = 1 if dpad_x == -1 else 0
        dp_right = 1 if dpad_x == 1 else 0
        channels[15] = 1000 + (((dp_up<<0)|(dp_down<<1)|(dp_left<<2)|(dp_right<<3))*100)

        # 4. TRANSMIT
        crsf_packet = pack_crsf_channels(channels)
        arduino.write(crsf_packet)

        # 5. FIXED REFRESHING TERMINAL PRINT
        print_counter += 1
        if print_counter >= 10:
            packet_str = f"STR:{channels[0]} | THR:{channels[1]} | RUD:{channels[2]}"
            # Clear line and print cleanly
            sys.stdout.write(f"\rPacket Data -> {packet_str}      ")
            sys.stdout.flush()
            print_counter = 0

        time.sleep(0.02)  # 50Hz update rate

except KeyboardInterrupt:
    print("\nStopping test mode via KeyboardInterrupt.")
finally:
    print("\nClosing serial port and cleaning up...")
    arduino.close()
    pygame.quit()