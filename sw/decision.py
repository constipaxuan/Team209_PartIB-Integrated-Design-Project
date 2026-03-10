
from locations import Location, Direction, Junctions, Target_Rack, Resistor_Color
from behaviour import Mode, Turn_Direction, Turn_State, Start_States, Delivery_Rack_States, Delivery_States
from lowerpurple_upper_orange_R_detect import * #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import * #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff
from test_motor import Motor
from utime import sleep
from time import ticks_ms, ticks_diff
from map_state import memory
from main import SR_sensor, turn_v4, Motion, line_follow_step, back_line_follow_step, detect_junction_type, turn_180
from R_pickup_N_measure import Pgram_tilt, grab, R_measure #variables & functions for R measurement and pickup

location = Location.start
direction = Direction.cw
mode = Mode.start
turn_complete = False
turn_state = Turn_State.start
turn_phase = 0
motion = Motion.follow
rack_junction_reached = False
target_rack = Target_Rack.orange_L #placeholder, should be determined by mapping and memory

#shld be defined in main code
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 

# Called when load has been dropped in required bay. Ends when turn_complete = True and line following starts again. Bot is now aligned with main loop spine and is oriented in the correct direction of travel.
main_spine_detected = False
def handler_blue_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase):
    if new_junction:
        main_spine_detected = True

    if not main_spine_detected:
        back_line_follow_step(S1, S2, 60, 20) #reverse until detect main spine again
    else:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)

        if target_rack == Target_Rack.purple_L:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.left, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
        else:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete, turn_phase = turn_180(Turn_Direction.left, S1, S2, turn_state, turn_phase, motor_l, motor_r) #turn 180 towards orange L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start

        if motion == Motion.follow:
            line_follow_step(S1, S2, 60, 20) 
        
    return main_spine_detected, motion, turn_state, turn_complete, turn_phase

def handler_red_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase):
    if new_junction:
        main_spine_detected = True

    if not main_spine_detected:
        back_line_follow_step(S1, S2, 60, 20) #reverse until detect main spine again
    else:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)

        if target_rack == Target_Rack.orange_L:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.right, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
        else:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete, turn_phase = turn_180(Turn_Direction.right, S1, S2, turn_state, turn_phase, motor_l, motor_r) #turn 180 towards orange L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start

        if motion == Motion.follow:
            line_follow_step(S1, S2, 60, 20) 
        
    return main_spine_detected, motion, turn_state, turn_complete, turn_phase

def handler_green_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase):
    if new_junction:
        main_spine_detected = True

    if not main_spine_detected:
        back_line_follow_step(S1, S2, 60, 20) #reverse until detect main spine again
    else:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)

        if target_rack == Target_Rack.purple_L:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.left, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
        else:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.right, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start

        if motion == Motion.follow:
            line_follow_step(S1, S2, 60, 20) 
        
    return main_spine_detected, motion, turn_state, turn_complete, turn_phase

def handler_yellow_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase):
    if new_junction:
        main_spine_detected = True

    if not main_spine_detected:
        back_line_follow_step(S1, S2, 60, 20) #reverse until detect main spine again
    else:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)

        if target_rack == Target_Rack.orange_L:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.right, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
        else:
            if new_junction and motion != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
            elif motion == Motion.turning:
                turn_state, turn_complete = turn_v4(Turn_Direction.left, S1, S2, turn_state, motor_l, motor_r) #turn left towards purple L
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start

        if motion == Motion.follow:
            line_follow_step(S1, S2, 60, 20) 
        
    return main_spine_detected, motion, turn_state, turn_complete, turn_phase

def search_mode(location):
    # I assume that this function is called when the bot should turn on the side sensor, I assume that the bot is already at the rack positions
    if location in [Location.rack_orange_U, Location.rack_purple_L]:
        if slot_status.count(1) < 6: #number of cleared slots is less than 6
            lowP_upperO_R_detect() #this keeps on running until the rack is cleared
            if R_detected:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay
                pass
    else:
        if slot_status.count(1) < 6: #number of cleared slots is less than 6
            upperP_lowO_R_detect() #this keeps on running until the rack is cleared
            if R_detected:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay (The else error above will go away once this function is added)
                pass

delivery_state = Delivery_States.pickup
ready_for_unloading = False 
# This function is called when the bot detects a load. It handles the entire pickup process up until the bot is back on the main loop spine ready to search for a new load.
def delivery_mode(S1, S2, SL, SR, location, direction, delivery_state, new_junction, resistor_color, turn_state, turn_complete):
    if location == Location.rack_orange_L:
        if delivery_state == Delivery_States.pickup:
            if ready_for_unloading == False:
                ready_for_unloading, turn_state, turn_complete, direction, deliv_state, motion, turn_dir, deliv_start_time, resistor_color = handler_orange_L_delivery(S1, S2, location, direction, junction_type, new_junction, resistor_color, turn_state, turn_complete)
            elif ready_for_unloading == True:
                ready_for_unloading = False #reset for next load
                delivery_state = Delivery_States.unloading
        
        if delivery_state == Delivery_States.unloading:
            LHS_dropoff(resistor_color)
            # Successful dropoff should output a signal and we can let delivery_state change to recover
        
        if delivery_state == Delivery_States.recover:
        #enter unloading bay with blue closest
        # LHS dropoff stops when load has been deposited
            if resistor_color == Resistor_Color.red:
                main_spine_detected, motion, turn_state, turn_complete, turn_phase = handler_red_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase)
            elif resistor_color == Resistor_Color.yellow:
                main_spine_detected, motion, turn_state, turn_complete, turn_phase = handler_yellow_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase)
            elif resistor_color == Resistor_Color.green:
                main_spine_detected, motion, turn_state, turn_complete, turn_phase = handler_green_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase)   
            elif resistor_color == Resistor_Color.blue:
                main_spine_detected, motion, turn_state, turn_complete, turn_phase = handler_blue_bay(main_spine_detected, S1, S2, new_junction, target_rack, motion, turn_state, turn_complete, turn_phase)

            if turn_complete:
                line_follow_step(S1, S2, 60, 20) #keep following the line and the bot should be in search mode again, ready to detect the next load.
                mode = Mode.search

    elif location == Location.rack_purple_L:
    #copy and paste later
        pass

deliv_state = Delivery_Rack_States.load_detected

def handler_orange_L_delivery(S1, S2, SL, SR, direction, new_junction, resistor_color, turn_state, turn_complete, motion, deliv_state, turn_dir, deliv_start_time):
    base = 60
    # Step 1: Enter delivery mode when laser detects a resistor load while bot is on a branch. 
    if deliv_state == Delivery_Rack_States.load_detected:
        if new_junction and motion != Motion.turning:
            if (SL == 0 and SR == 0): # move forward until we lose the white line.
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                motion = Motion.turning
                turn_state = Turn_State.start
                if direction == Direction.cw:
                    turn_dir = Turn_Direction.right
                elif direction == Direction.acw:
                    turn_dir = Turn_Direction.left
        
        if motion == Motion.turning:
            if not turn_complete:
                turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state)
            else:
                motion = Motion.follow
                turn_complete = False
                turn_state = Turn_State.start
                deliv_state = Delivery_Rack_States.approaching
                deliv_start_time = ticks_ms() #start timer for how long we have been in delivery mode
        
    #Step 2: Move forward closer to resistor
    elif deliv_state == Delivery_Rack_States.approaching:
        line_follow_step(S1, S2, base, 20) 
        if ticks_diff(ticks_ms(), deliv_start_time) > 500: #approach for 0.5 seconds, then stop and grab. Time can be adjusted based on testing
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            deliv_state = Delivery_Rack_States.reached

    # Step 3: Grab the load. Adjust timing so that the claw can shut before the bot starts reversing.
    elif deliv_state == Delivery_Rack_States.reached:
        grab() 
        resistor_color = R_measure() #measure the resistor color and store it as a variable so that the bot knows which bay to drop it off at
        deliv_state = Delivery_Rack_States.retracting
        # Step 4: Reverse until RL junction is detected. Then turn right towards the drop off bay.

        #move forward until you grab. After grabbing reverse until reach RL junction, turn 90 deg right (cw)
    elif deliv_state == Delivery_Rack_States.retracting:
        back_line_follow_step(S1, S2, base, 20) #reverse until detect main spine again

        if new_junction and (SL == 1 and SR == 1): #detect RL junction. No need to lose the white line bc we are approaching in reverse
            deliv_state = Delivery_Rack_States.reorienting
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            motion = Motion.turning
            turn_state = Turn_State.start
            turn_dir = Turn_Direction.right
            direction = Direction.acw
        
    elif deliv_state == Delivery_Rack_States.reorienting:
        if motion == Motion.turning:
            if not turn_complete:
                turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state)
            else:
                motion = Motion.follow
                turn_complete = False
                turn_state = Turn_State.start
            
        if motion == Motion.follow:
            line_follow_step(S1, S2, 60, 20) 
        
            #rack_branches_OL is known
            if new_junction and SL == 1:
                memory["rack_branches_OL"] -= 1
                if memory["rack_branches_OL"] % 6 == 0:
                    deliv_state = Delivery_Rack_States.load_detected #reset to search for next load after passing each branch, since each bay has 6 branches. 
                    return True, turn_state, turn_complete, direction, deliv_state, motion, turn_dir, deliv_start_time, resistor_color
        
    return False, turn_state, turn_complete, direction, deliv_state, motion, turn_dir, deliv_start_time, resistor_color

# Call format: 
# ready_for_unloading, turn_state, turn_complete, direction, deliv_state, motion, turn_dir, deliv_start_time, resistor_color = handler_orange_L_delivery(S1, S2, location, direction, junction_type, new_junction, resistor_color, turn_state, turn_complete)



