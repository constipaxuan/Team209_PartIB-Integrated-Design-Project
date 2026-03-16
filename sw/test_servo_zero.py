from machine import Pin, PWM
import time

servo = PWM(Pin(13))
servo.freq(50)

# We must track the current position in software
current_claw_angle = 135 

def set_angle(angle):
    angle = max(0, min(270, angle))
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)

def move_claw_slowly(target_angle, speed_delay=0.02):
    """
    speed_delay: seconds between each degree. 
    0.01 is brisk, 0.05 is very slow and cautious.
    """
    global current_claw_angle
    
    # Determine if we are moving up or down
    step = 1 if target_angle > current_claw_angle else -1
    
    # Move one degree at a time
    for angle in range(int(current_claw_angle), int(target_angle) + step, step):
        set_angle(angle)
        time.sleep(speed_delay) # This creates the 'slow' effect
        
    current_claw_angle = target_angle
    print(f"Claw arrived at {target_angle}")

# --- CAUTIOUS TEST ---
print("Starting cautious test...")
set_angle(current_claw_angle) # Sync hardware to our starting variable

# Slowly move to 200 degrees (maybe that's 'open')
move_claw_slowly(200, speed_delay=0.05) 
time.sleep(1)

# Slowly move to 50 degrees (maybe that's 'closed')
move_claw_slowly(50, speed_delay=0.05)