from machine import Pin, PWM
import time

#now testing the claw
#set servo on PWM pin 13
servo = PWM(Pin(13))
servo.freq(50) # Standard 50Hz frequency

def set_angle(angle):
    # Map 0-270 degrees to 500-2500 microseconds
    # Pico PWM duty is 0-65535. 
    # 50Hz period is 20ms. 500us = 2.5% duty. 2500us = 12.5% duty.
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)

# Test Sweep
while True:
    print("Moving to 0 degrees")
    set_angle(0)
    time.sleep(1)
    
    print("Moving to 270 degrees")
    set_angle(270)
    time.sleep(1)