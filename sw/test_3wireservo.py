from machine import Pin, PWM
from time import ticks_ms, ticks_diff, sleep
CLAW_OPERATION_DURATION = 4000
#now testing the claw
#set servo on PWM pin 13
servo_claw = PWM(Pin(13))
servo_claw.freq(50) # Standard 50Hz frequency




# --- MEMORY VARIABLES ---
# Initialize at 135 (your idle/open position)
current_claw_angle = 135 
claw_move_done = False 

def set_angle_slow(current_angle, target_angle, speed_delay):
    # Efficiency check: If we are already there, don't do anything
    if current_angle == target_angle:
        return target_angle

    step = 1 if target_angle > current_angle else -1
    
    for angle in range(current_angle, target_angle + step, step):
        pulse_width = 500 + (angle / 270) * 2000
        duty = int((pulse_width / 20000) * 65535)
        
        servo_claw.duty_u16(duty)
        sleep(speed_delay)
    return target_angle 

def grab(claw_move_done):
    start_time = ticks_ms()
    while ticks_diff(ticks_ms(), start_time) < CLAW_OPERATION_DURATION:
            """Moves the claw from its current position to 90 degrees."""
            global current_claw_angle
            current_claw_angle = set_angle_slow(current_claw_angle, 90, 0.01)

def release():
    start_time = ticks_ms()
    while ticks_diff(ticks_ms(), start_time) < CLAW_OPERATION_DURATION:
            """Moves the claw from its current position to 160 degrees."""
            global current_claw_angle
            current_claw_angle = set_angle_slow(current_claw_angle, 160, 0.01)

# --- MAIN LOOP ---
grab()
sleep(1)
release()
        
    # The rest of your line following code runs here...