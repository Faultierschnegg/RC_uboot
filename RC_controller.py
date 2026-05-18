import os
import time
#import serial später wieder reinmachen wenn eingesteckt mit tx


#os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

print("running without arduino")

pygame.init()
pygame.joystick.init()

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
print("Move your joysticks to see the data change. Press Ctrl+C to stop.\n")

try:
    while True:
        pygame.event.pump()
        # 1. READ STICKS (Axes)
        steering_axis = controller.get_axis(0)
        throttle_axis = controller.get_axis(1)  # Left Stick Y
        rud_axis = controller.get_axis(3)
        rrl_axis = controller.get_axis(2)  # Right Stick X
        lt_bumper = controller.get_axis(4)
        rt_bumper = controller.get_axis(5)

        throttle = map_value(-throttle_axis, -1.0, 1.0)
        steering = map_value(steering_axis, -1.0, 1.0)
        rud = map_value(-rud_axis, -1.0, 1.0)
        rrl = map_value(rrl_axis, -1.0, 1.0)


        #get button inputs A,X,Y,B,
        a_button_state = controller.get_button(0) 
        b_button_state = controller.get_button(1)
        x_button_state = controller.get_button(2)
        y_button_state = controller.get_button(3)
        lb_bumper_state = controller.get_button(4)
        rb_bumper_state = controller.get_button(5)
        minus_bumper_state = controller.get_button(6)
        cross_bumper_state = controller.get_button(7)

        # Map the 0 or 1 button state to RC standards (1000us or 2000us)
        ch3 = 2000 if a_button_state == 1 else 1000
        ch4 = 2000 if b_button_state == 1 else 1000
        ch5 = 2000 if x_button_state == 1 else 1000
        ch6 = 2000 if y_button_state == 1 else 1000
        ch7 = 2000 if lb_bumper_state == 1 else 1000
        ch8 = 2000 if rb_bumper_state == 1 else 1000
        ch9 = 2000 if minus_bumper_state == 1 else 1000
        ch10 = 2000 if cross_bumper_state == 1 else 1000 

        # Optional: Read the D-pad (called a "Hat" in Pygame)
        # get_hat(0) returns a tuple like (x, y). E.g., (0, 1) is UP, (-1, 0) is LEFT
        dpad_state = controller.get_hat(0) 

        # Package data into our 4-channel CSV string format
        packet = f"{steering},{throttle},{rud},{rrl},{rt_bumper},{lt_bumper},{ch3},{ch4},{ch5},{ch6},{ch7},{ch8},{ch9},{ch10},{dpad_state}"



        # Debug print showing sticks and buttons
        print(f"Packet: [{packet}] | A-Btn: {a_button_state} | RB-Bumper: {rb_bumper_state}   ", end="\r")

        time.sleep(0.02)  # 50Hz update rate


except KeyboardInterrupt:
    print("\nStopping test mode.")
finally:
    # --- REMOVED ARDUINO.CLOSE ---
    # arduino.close()
    pygame.quit()