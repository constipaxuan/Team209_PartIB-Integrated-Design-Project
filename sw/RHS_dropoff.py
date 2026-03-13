
from behaviour import Turn_Direction, Turn_State, Unloading_States
from locations import Junctions, Resistor_Color
from main import S1, S2, SR, SL, detect_junction_type, turn_v4, line_follow_step, Motion, motor_l, motor_r
from R_pickup_N_measure import release
from decision import sensors, robot, events, delivery

target_bay = 0 
drop_off_bay = 0
bay_latch = False # This is our "latch"
turn_dir = Turn_Direction.nil
motion = Motion.follow
prev_on_junction = False
prev_on_T = False

on_junction = (SL == 1 or SR == 1)
new_junction = (not prev_on_junction) and on_junction
on_T = (SL == 1 and SR == 1)
new_T = (not prev_on_T) and on_T
unloading_state = Unloading_States.finding_bay

# Ends when unloading_state == Unloading_States.done. Before calling again need to reset unloading_state 
def LHS_dropoff(sensors, events, robot, delivery):
    # ASSIGNING TARGET BAY
    if delivery["resistor_color"] == Resistor_Color.red: 
        delivery["target_bay"] = 4 # Red, which is the rightmost bay
    elif delivery["resistor_color"] == Resistor_Color.yellow: 
        delivery["target_bay"] = 3 # Yellow
    elif delivery["resistor_color"] == Resistor_Color.green: 
        delivery["target_bay"] = 1 # Green, skip 1 to skip the starting box
    elif delivery["resistor_color"] == Resistor_Color.blue: 
        delivery["target_bay"] = 0 # Blue


    # State machine 
    if delivery["unloading_state"] == Unloading_States.finding_bay:
            
        # TARGET DETECTION  
        # case when the target bay is blue, no need to turn -- blue bay is literally straight ahead. 
        if delivery["target_bay"] == 0:
            if events["new_junction"]: # 1st junction reached.
                delivery["unloading_state"] = Unloading_States.found_bay
                
        elif delivery["target_bay"] != 0:
        # Turning into unloading corridoor if target bay is not blue. Motion = turning when correct bay is found. Handled in decision loop.
            if events["new_junction"] and robot["motion"] != Motion.turning:
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
                robot["turn_dir"] = Turn_Direction.left
                    
    elif delivery["target_bay"] != 0 and delivery["unloading_state"] == Unloading_States.counting_bays:
        if sensors["SL"] == 1 and not delivery["bay_latch"]: # if new_junction: (includes NOt doublecounting)
            delivery["drop_off_bay"] += 1
            delivery["bay_latch"] = True # Block further counting until we leave the line
            #print(f"Passing branch {drop_off_bay}")
        
        
        if sensors["SL"] == 0:
            delivery["bay_latch"] = False # Reset the latch once we are back on black

        if delivery["drop_off_bay"] == delivery["target_bay"] and robot["motion"] != Motion.turning:
            print("Target reached! Turning into bay")
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            robot["turn_dir"] = Turn_Direction.right

    elif delivery["unloading_state"] == Unloading_States.found_bay:
        if events["new_T"]: #arrived at box
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            release() #release grabber
            delivery["unloading_state"] = Unloading_States.done
    
    # Motion Control: Called exactly ONCE per iteration
    if robot["motion"] == Motion.follow:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
    elif robot["motion"] == Motion.turning:
        robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn into box
        if robot["turn_complete"]:
            robot["turn_state"] = Turn_State.start #reset turn state for next turn
            robot["turn_complete"] = False
            robot["motion"] = Motion.follow 
            
            if delivery["unloading_state"] == Unloading_States.finding_bay:
                delivery["unloading_state"] = Unloading_States.counting_bays
            elif delivery["unloading_state"] == Unloading_States.counting_bays:
                delivery["unloading_state"] = Unloading_States.found_bay







"""      # 1. Line following code goes here (keep the car on the main spine)
    line_follow_step(S1, S2) 
    # 2. Check for branches
    while True:
        if SR == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
            
        if SR == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        # case when the target bay is red, no need to turn
        if target_bay == 0: 
            if detect_junction_type == Junctions.RL: # Went straight and arrived at blue box
                #stop car 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                break
        if target_bay != 0:
            if detect_junction_type == Junctions.R:
                turn_v4(Turn_Direction.left, S1, S2, turn_state) #turn into bay corridor
                line_follow_step(S1, S2)
            if drop_off_bay == target_bay:
                print("Target reached! Turning into bay")
                turn_v4(Turn_Direction.left, S1, S2, turn_state) #turn into box
                line_follow_step(S1, S2) #line follow into box
                if detect_junction_type == Junctions.RL: #arrived at box
                    #stop car 
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    break
    release() #release grabber """