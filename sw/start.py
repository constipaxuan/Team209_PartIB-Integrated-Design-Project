from test_motor import Motor
from machine import Pin
from utime import sleep_ms

base = 70
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 
counting = True
start_T_shape_count = 0

def update_start_T_count():
    global start_T_shape_count, counting
    if SL == 1 and SR == 1 and counting:
        start_T_shape_count += 1
        counting = False # Latch on
        print(f"Junction Detected! Total: {start_T_shape_count}")
    elif SL == 0 and SR == 0:
        counting = True # Ready for next junction

def get_out_of_box():
    # --- Main Mission Loop ---
    while True:
        update_start_T_count()
        
        # State 1: Drive out of the box, drive straight
        if start_T_shape_count < 2:
            motor_l.Forward(base)
            motor_r.Forward(base)

        # State 2: Hit second T shape, turn clockwise
        elif start_T_shape_count == 2:
            print("Turning Clockwise into corridor...")
            motor_l.Forward(base)
            motor_r.Reverse(base)
            sleep_ms(600) # Adjust this time so it clears the T-junction
            motor_l.Forward(base)
            motor_r.Forward(base)
            start_T_shape_count = 2.1 # Increment to avoid re-triggering this state
            
        # State 3: Hit third T shape, turn anti-clockwise
        elif start_T_shape_count > 3:
            print("Turning Anti-clockwise into rack...")
            motor_l.Reverse(base)
            motor_r.Forward(base)
            sleep_ms(600)
            motor_l.Forward(base)
            motor_r.Forward(base)
            print("Arrived at the Purple Rack.")
            break # Exit this navigation loop to start scanning