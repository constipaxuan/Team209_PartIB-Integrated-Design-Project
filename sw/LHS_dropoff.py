# Coming from the LHS main spine back down to loading bays
# Red = 0, Yellow = 1, SKIP the starting box = 2, Green = 3, Blue = 4

from sw.behaviour import Turn_Direction
from sw.locations import Junctions, Resistor_Color
from sw.main import S1, S2, SR, detect_junction_type, turn_v4, line_follow_step
from R_pickup_N_measure import release

target_bay = 0 
drop_off_bay = 0
counting_line = False # This is our "latch"

on_junction = (SL == 1 or SR == 1)
new_junction = (not prev_on_junction) and on_junction

def LHS_dropoff(resistor_color):
    if resistor_color == Resistor_Color.red: 
        target_bay = 4 # Red, which is the rightmost bay
    if resistor_color == Resistor_Color.yellow: 
        target_bay = 3 # Yellow
    if resistor_color == Resistor_Color.green: 
        target_bay = 1 # Green, skip 1 to skip the starting box
    if resistor_color == Resistor_Color.blue: 
        target_bay = 0 # Blue


    # 1. Line following code goes here (keep the car on the main spine)
    line_follow_step(S1, S2, 60, 20) # Placeholder for line following function, replace with actual function
    # 2. Check for branches
    while True:
        if SR == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
            
        if SR == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        # case when the target bay is blue, no need to turn
        if target_bay == 0: 
            if detect_junction_type == Junctions.RL: # Went straight and arrived at blue box
                #stop car 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                break
        if target_bay != 0:
            if detect_junction_type == Junctions.L:
                turn_v4(Turn_Direction.left, S1, S2, turn_state) #turn into bay corridor
                line_follow_step(S1, S2)
            if drop_off_bay == target_bay:
                print("Target reached! Turning into bay")
                turn_v4(Turn_Direction.right, S1, S2, turn_state) #turn into box
                line_follow_step(S1, S2) #line follow into box
                if detect_junction_type == Junctions.RL: #arrived at box
                    #stop car 
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    break
    release() #release grabber

