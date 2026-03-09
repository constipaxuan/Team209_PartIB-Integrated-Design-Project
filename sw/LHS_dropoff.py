# Coming from the LHS main spine back down to loading bays
# Red = 0, Yellow = 1, SKIP the starting box = 2, Green = 3, Blue = 4

from sw.behaviour import Turn_Direction, Turn_State, Unloading_States
from sw.locations import Junctions, Resistor_Color
from sw.main import S1, S2, SR, detect_junction_type, turn_v4, line_follow_step, Motion, motor_l, motor_r
from R_pickup_N_measure import release

target_bay = 0 
drop_off_bay = 0
counting_line = False # This is our "latch"

on_junction = (SL == 1 or SR == 1)
new_junction = (not prev_on_junction) and on_junction
unloading_state = Unloading_States.finding_bay

def LHS_dropoff(resistor_color, turn_state, turn_complete):
    if resistor_color == Resistor_Color.red: 
        target_bay = 4 # Red, which is the rightmost bay
    if resistor_color == Resistor_Color.yellow: 
        target_bay = 3 # Yellow
    if resistor_color == Resistor_Color.green: 
        target_bay = 1 # Green, skip 1 to skip the starting box
    if resistor_color == Resistor_Color.blue: 
        target_bay = 0 # Blue


    # 1. Line following code goes here (keep the car on the main spine)
    if motion == Motion.follow:
        line_follow_step(S1, S2, 60, 20) # Placeholder for line following function, replace with actual function
    # 2. Check for branches
    if unloading_state == Unloading_States.finding_bay:
        if SR == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
        
        
        if SR == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        # case when the target bay is blue, no need to turn
        if target_bay == 0: 
            unloading_state = Unloading_States.found_bay
                
        if target_bay != 0:
        # Turning into unloading corridoor if target bay is not blue.
            if detect_junction_type == Junctions.L:
                if motion == Motion.turning:
                    turn_state, turn_complete = turn_v4(Turn_Direction.left, S1, S2, turn_state, motor_l, motor_r) #turn into bay corridor
                    if turn_complete:
                        turn_state = Turn_State.start #reset turn state for next turn
                        turn_complete = False
                        motion = Motion.follow #switch back to line following after turn
            if motion == Motion.follow:
                line_follow_step(S1, S2, 60, 20) 

            if drop_off_bay == target_bay:
                print("Target reached! Turning into bay")
                motion = Motion.turning
                if motion == Motion.turning:
                    turn_state, turn_complete = turn_v4(Turn_Direction.right, S1, S2, turn_state, motor_l, motor_r) #turn into box
                    if turn_complete:
                        turn_state = Turn_State.start #reset turn state for next turn
                        turn_complete = False
                        motion = Motion.follow 
                        unloading_state = Unloading_States.found_bay
                if motion == Motion.follow:
                    line_follow_step(S1, S2, 60, 20) #line follow into box

    if unloading_state == Unloading_States.found_bay:
        if detect_junction_type == Junctions.RL: #arrived at box
            #stop car 
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            release() #release grabber
                

""" def LHS_dropoff(resistor_color, turn_state, turn_complete):
    if resistor_color == Resistor_Color.red: 
        target_bay = 4 # Red, which is the rightmost bay
    if resistor_color == Resistor_Color.yellow: 
        target_bay = 3 # Yellow
    if resistor_color == Resistor_Color.green: 
        target_bay = 1 # Green, skip 1 to skip the starting box
    if resistor_color == Resistor_Color.blue: 
        target_bay = 0 # Blue


    # 1. Line following code goes here (keep the car on the main spine)
    if motion == Motion.follow:
        line_follow_step(S1, S2, 60, 20) # Placeholder for line following function, replace with actual function
    # 2. Check for branches
    if unloading_state == Unloading_States.finding_bay:
        if SR == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
            
        if SR == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        # case when the target bay is blue, no need to turn
        if target_bay == 0: 
            unloading_state = Unloading_States.found_bay
                
        if target_bay != 0:
        # Turning into unloading corridoor if target bay is not blue.
            if detect_junction_type == Junctions.L:
                if motion == Motion.turning:
                    turn_state, turn_complete = turn_v4(Turn_Direction.left, S1, S2, turn_state, motor_l, motor_r) #turn into bay corridor
                    if turn_complete:
                        turn_state = Turn_State.start #reset turn state for next turn
                        turn_complete = False
                        motion = Motion.follow #switch back to line following after turn
            if motion == Motion.follow:
                line_follow_step(S1, S2, 60, 20) 

            if drop_off_bay == target_bay:
                print("Target reached! Turning into bay")
                motion = Motion.turning
                if motion == Motion.turning:
                    turn_state, turn_complete = turn_v4(Turn_Direction.right, S1, S2, turn_state, motor_l, motor_r) #turn into box
                    if turn_complete:
                        turn_state = Turn_State.start #reset turn state for next turn
                        turn_complete = False
                        motion = Motion.follow 
                        unloading_state = Unloading_States.found_bay
                if motion == Motion.follow:
                    line_follow_step(S1, S2, 60, 20) #line follow into box

    if unloading_state == Unloading_States.found_bay:
        if detect_junction_type == Junctions.RL: #arrived at box
            #stop car 
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            release() #release grabber """