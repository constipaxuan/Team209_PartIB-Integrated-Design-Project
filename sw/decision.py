
from locations import Location, Direction, Junctions, Target_Rack, Resistor_Color
from behaviour import Mode, Turn_Direction, Turn_State, Start_States, Delivery_Rack_States, Delivery_States, Unloading_States
from lowerpurple_upper_orange_R_detect import * #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import * #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff
from test_motor import Motor
from utime import sleep
from time import ticks_ms, ticks_diff
from map_state import memory
from main import SR_sensor, turn_v4, Motion, line_follow_step, back_line_follow_step, detect_junction_type, turn_180, TNT_states
from R_pickup_N_measure import Pgram_tilt, grab, R_measure #variables & functions for R measurement and pickup


#shld be defined in main code
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 

# Required transitions: ready for unloading (local rack handler --> dropoff). unloading_state == done (dropoff --> local bay handler)
# re-read every iteration.


target_racks = [Location.rack_purple_L, Location.rack_orange_L, Location.rack_purple_U, Location.rack_orange_U]
target_rack_idx = 0

# --- TIMED TURNS + FINAL ALIGNMENT FOR RACK BRANCH EXIT ---
def timed_turn_step(robot):
    if not robot["timed_turn_started"]:
        robot["timed_turn_started"] = True
        robot["timed_turn_start"] = ticks_ms()

    if robot["turn_dir"] == Turn_Direction.left:
        motor_l.Forward(speed=60)
        motor_r.Forward(speed=20)
    elif robot["turn_dir"] == Turn_Direction.right:
        motor_l.Forward(speed=20)
        motor_r.Forward(speed=60)

    if ticks_diff(ticks_ms(), robot["timed_turn_start"]) > 300:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        robot["motion"] = Motion.follow
        robot["timed_turn_started"] = False
        return True

    return False
# robot["turn_complete"] = timed_turn_step(robot). Exit when turn is complete

# --- LOCAL BAY HANDLERS ---
# Called when load has been dropped in required bay. Ends when turn_complete = True and line following starts again. Bot is now aligned with main loop spine and is oriented in the correct direction of travel.
# I am assuming that new_junction will not trigger on the one the bot is already sitting on. 
def handler_blue_bay(sensors, events, robot, delivery):
    
    if events["new_junction"]:
        delivery["main_spine_detected"] = True

    if not delivery["main_spine_detected"] :
        back_line_follow_step(sensors["S1"], sensors["S2"], 80, 20) #reverse until detect main spine again
    
    else:
        if delivery["target_rack"] == Target_Rack.purple_L:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn left towards purple L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
        else:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"], delivery["turn_phase"] = turn_180(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], delivery["turn_phase"], motor_l, motor_r) #turn 180 towards orange L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start

        if robot["motion"] == Motion.follow:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20) 

def handler_red_bay(sensors, events, robot, delivery):
    
    if events["new_junction"]:
        delivery["main_spine_detected"] = True

    if not delivery["main_spine_detected"] :
        back_line_follow_step(sensors["S1"], sensors["S2"], 80, 20) #reverse until detect main spine again
    
    else:
        if delivery["target_rack"] == Target_Rack.orange_L:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn left towards purple L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
        else:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"], delivery["turn_phase"] = turn_180(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], delivery["turn_phase"], motor_l, motor_r) #turn 180 towards orange L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start

        if robot["motion"] == Motion.follow:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20) 

def handler_green_bay(sensors, events, robot, delivery):
    
    if events["new_junction"]:
        delivery["main_spine_detected"] = True

    if not delivery["main_spine_detected"] :
        back_line_follow_step(sensors["S1"], sensors["S2"], 80, 20) #reverse until detect main spine again
    
    else:
        if delivery["target_rack"] == Target_Rack.purple_L:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn left towards purple L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
        else:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn 180 towards orange L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start

        if robot["motion"] == Motion.follow:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20) 

def handler_yellow_bay(sensors, events, robot, delivery):
    
    if events["new_junction"]:
        delivery["main_spine_detected"] = True

    if not delivery["main_spine_detected"] :
        back_line_follow_step(sensors["S1"], sensors["S2"], 80, 20) #reverse until detect main spine again
    
    else:
        if delivery["target_rack"] == Target_Rack.purple_L:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn left towards purple L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
        else:
            if events["new_junction"] and robot["motion"] != Motion.turning: 
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
            elif robot["motion"] == Motion.turning:
                robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn 180 towards orange L
                if robot["turn_complete"]:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start

        if robot["motion"] == Motion.follow:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20) 

# --- OVERALL DELIVERY MODE FROM EACH RACK ---
def delivery_from_orange_L(sensors, events, robot, delivery):
    if delivery["delivery_state"] == Delivery_States.pickup:
        if delivery["ready_for_unloading"] == False:
            handler_orange_L_delivery(sensors, events, robot, delivery)
        elif delivery["ready_for_unloading"] == True:
            delivery["ready_for_unloading"] = False #reset for next load
            delivery["delivery_state"] = Delivery_States.unloading
        
    elif delivery["delivery_state"] == Delivery_States.unloading:
        LHS_dropoff(sensors, events, robot, delivery) 
        # Successful dropoff should output a signal and we can let delivery_state change to recover
        if delivery["unloading_state"] == Unloading_States.done:
            delivery["delivery_state"] = Delivery_States.recover
            delivery["unloading_state"] = Unloading_States.finding_bay #reset unloading state for next time
        
    elif delivery["delivery_state"] == Delivery_States.recover:
    #enter unloading bay with blue closest
    # LHS dropoff stops when load has been deposited
        if delivery["resistor_color"] == Resistor_Color.red:
            handler_red_bay(sensors, events, robot, delivery)
        elif delivery["resistor_color"] == Resistor_Color.yellow:
            handler_yellow_bay(sensors, events, robot, delivery)
        elif delivery["resistor_color"] == Resistor_Color.green:
            handler_green_bay(sensors, events, robot, delivery)   
        elif delivery["resistor_color"] == Resistor_Color.blue:
            handler_blue_bay(sensors, events, robot, delivery)

        if robot["turn_complete"]:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20) #keep following the line and the bot should be in search mode again, ready to detect the next load.
            robot["mode"] = Mode.search
            delivery["main_spine_detected"] = False
            robot["turn_complete"] = False #reset
            delivery["delivery_state"] = Delivery_States.pickup

# --- LOCAL RACK HANDLERS  
def handler_orange_L_delivery(sensors, events, robot, delivery):
    # Step 1: Enter delivery mode when laser detects a resistor load while bot is on a branch. 
    if delivery["rack_state"] == Delivery_Rack_States.load_detected:
        if events["new_junction"] and robot["motion"] != Motion.turning:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            if robot["direction"] == Direction.cw:
                robot["turn_dir"] = Turn_Direction.right
            elif robot["direction"] == Direction.acw:
                robot["turn_dir"] = Turn_Direction.left
        
        if robot["motion"] == Motion.turning:
            robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) 
            if robot["turn_complete"]:
                robot["motion"] = Motion.follow
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                delivery["rack_state"] = Delivery_Rack_States.reached
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
    

def handler_purple_L_delivery(sensors, events, robot, delivery):
    # Step 1: Enter delivery mode when laser detects a resistor load while bot is on a branch. 
    if delivery["rack_state"] == Delivery_Rack_States.load_detected:
        if events["new_junction"] and robot["motion"] != Motion.turning:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            if robot["direction"] == Direction.cw:
                robot["turn_dir"] = Turn_Direction.right
            elif robot["direction"] == Direction.acw:
                robot["turn_dir"] = Turn_Direction.left
        
        if robot["motion"] == Motion.turning:
            robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) 
            if robot["turn_complete"]:
                robot["motion"] = Motion.follow
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                delivery["rack_state"] = Delivery_Rack_States.reached
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)

    # Step 3: Grab the load. Adjust timing in R_measure so that the claw can shut before the bot starts reversing. atp IDGAF is this part is blocking.
    elif delivery["rack_state"] == Delivery_Rack_States.reached:
        grab() 
        delivery["resistor_color"] = R_measure() #measure the resistor color and store it as a variable so that the bot knows which bay to drop it off at
        delivery["rack_state"] = Delivery_Rack_States.reorienting
        robot["motion"] = Motion.turning
        robot["turn_dir"] = Turn_Direction.left # Face the unloading bay.
        robot["timed_turn_started"] = False
    
    # Step 4: No need to reverse. No space.
        
    elif delivery["rack_state"] == Delivery_Rack_States.reorienting:
        if robot["motion"] == Motion.turning:
            robot["turn_complete"] = timed_turn_step(robot)
            if robot["turn_complete"]:
                robot["motion"] = Motion.follow
                robot["turn_complete"] = False
                robot["timed_turn_started"] = False
            
        elif robot["motion"] == Motion.follow:
            back_line_follow_step(sensors["S1"], sensors["S2"], 80, 20) 
            if events["new_T"]:
                delivery["rack_state"] = Delivery_Rack_States.reoriented
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                memory["rack_branches_PL"] = 0
    
    elif delivery["rack_state"] == Delivery_Rack_States.reoriented:
        if events["new_junction"]: # Detect SL HIGHs. No other junctions to be confused with so this is fine.
            memory["rack_branches_PL"] += 1
            if memory["rack_branches_PL"] == 6:
                delivery["rack_state"] = Delivery_Rack_States.load_detected #reset to search for next load after passing each branch, since each bay has 6 branches.
                delivery["ready_for_unloading"] = True 
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
    
                    

# Call format: 
# ready_for_unloading, turn_state, turn_complete, direction, deliv_state, motion, turn_dir, deliv_start_time, resistor_color = handler_orange_L_delivery(S1, S2, location, direction, junction_type, new_junction, resistor_color, turn_state, turn_complete)

    # I DON'T THINK THE BOT NEEDS TO MOVE ANYMORE. IT IS CLOSE ENOUGH AS IT IS. MIGHT EVEN NEED TO MOVE BACK.
    """ elif delivery["rack_state"] == Delivery_Rack_States.approaching:
        line_follow_step(sensors["S1"], sensors["S2"], base, 20) 
        if ticks_diff(ticks_ms(), delivery["deliv_start_time"]) > 500: #approach for 0.5 seconds, then stop and grab. Time can be adjusted based on testing
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            delivery["rack_state"] = Delivery_Rack_States.reached """

    #move forward until you grab. After grabbing reverse until reach RL junction, turn 90 deg right (cw)
    """ elif delivery["rack_state"] == Delivery_Rack_States.retracting:
        back_line_follow_step(sensors["S1"], sensors["S2"], base, 20) 
          if events["new_T"]: #detect RL junction. No need to lose the white line bc we are approaching in reverse
            delivery["rack_state"] = Delivery_Rack_States.reorienting
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            robot["turn_dir"] = Turn_Direction.right
            robot["direction"] = Direction.acw
        """ #reverse until detect main spine again

# Idea: Search mode we go:
# 1. Lower Purple
# 2. Lower Orange
# 3. Upper Purple
# 4. Upper Orange
# Target rack remains the same until ALL slots are cleared. 
def search_mode(sensors, events, robot, delivery):
    # I assume that this function is called when the bot should turn on the side sensor, I assume that the bot is already at the rack positions
    delivery["target_rack"] = target_racks[robot["target_rack_idx"]]

    if robot["location"] in [Location.rack_orange_U, Location.rack_purple_L]:
        if delivery["slot_status"].count(1) < 6: #number of cleared slots is less than 6
            lowP_upperO_R_detect(sensors, events, robot, delivery) #this keeps on running until the rack is cleared
            if delivery["R_detected"]:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay
                robot["mode"] = Mode.delivery
                delivery["R_detected"] = False
                return
    elif robot["location"] in [Location.rack_orange_L, Location.rack_purple_U]:
        if delivery["slot_status"].count(1) < 6: #number of cleared slots is less than 6
            upperP_lowO_R_detect(sensors, events, robot, delivery) #this keeps on running until the rack is cleared
            if delivery["R_detected"]:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay (The else error above will go away once this function is added)
                robot["mode"] = Mode.delivery
                delivery["R_detected"] = False
                return
        
    
    # After one (lower floor) rack is cleared -- Switching racks. This is just for FIRST COMPETITION. Only enter elevator_low if lower rack is cleared.
    elif robot["location"] == Location.elevator_low:
        if delivery["target_rack"] == Location.rack_orange_L:
            robot["direction"] = Direction.acw
            if events["new_junction"]:
                delivery["rack_switching_bcount"] += 1
            if delivery["rack_switching_bcount"] == 3 and robot["motion"] != Motion.turning:
                robot["motion"] = Motion.turning
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                delivery["rack_switching_bcount"] = 0
                robot["turn_dir"] = Turn_Direction.left
    
    # Reset each time in unloading bay --- Takes slightly longer but simplifies logic significantly
    elif robot["location"] == Location.unloading:
        delivery["slot_status"] = [0,0,0,0,0,0]

    # --- MOTION HANDLERS ---
    if robot["motion"] == Motion.turning:
        robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) 
        if robot["turn_complete"]:
            robot["motion"] = Motion.follow
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
    if robot["motion"] == Motion.follow:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)



# This function is called when the bot detects a load. It handles the entire pickup process up until the bot is back on the main loop spine ready to search for a new load.
def delivery_mode(sensors, events, robot, delivery):
    if robot["location"] == Location.rack_orange_L:
        delivery_from_orange_L(sensors, events, robot, delivery)

    elif robot["location"] == Location.rack_purple_L:
        pass




# --- TEST ---

memory["rack_branches_OL"] = 4 # Arbitrary number -- Start 4th closest to unloading bay