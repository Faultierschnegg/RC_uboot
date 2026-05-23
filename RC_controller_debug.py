import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller found.")
    exit()

controller = pygame.joystick.Joystick(0)
controller.init()

print(f"Testing: {controller.get_name()}")
print(f"Total Axes: {controller.get_numaxes()} | Total Buttons: {controller.get_numbuttons()}")

try:
    while True:
        pygame.event.pump()
        
        # Print all axis values
        axes_str = " | ".join([f"Axis {i}: {controller.get_axis(i):.2f}" for i in range(controller.get_numaxes())])
        
        # Print any pressed buttons
        buttons_pressed = [i for i in range(controller.get_numbuttons()) if controller.get_button(i)]
        
        print(f"{axes_str} || Buttons Pressed: {buttons_pressed}", end="\r")
        time.sleep(0.1)
except KeyboardInterrupt:
    pygame.quit()