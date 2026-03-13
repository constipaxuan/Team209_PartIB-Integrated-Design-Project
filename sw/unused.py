#Code for detecting whether there is a resistor or not for each slot
def R_detect(events, laser_distance, delivery, robot):
#QN: after I detect a resistor, how do I connect the turning function after this? Turning left or right to collect a resistor depends on the rack
    # ONLY act if this is a BRAND NEW junction detection (Does the new junction work here?)
    if events["new_junction"] and not events["new_T"]:
        # decide which distance sensor to use based on direction of travel
        # 1. Safety check: stop the counter if we run out of slots (All slots have been cleared for a particular rack)
        if delivery["search_slot_counter"] >= 6: # 6 slots
            delivery["rack_cleared"] = True
            robot["target_rack_idx"] += 1
            delivery["search_slot_counter"] = 0
            delivery["slot_status"] = [0,0,0,0,0,0] #still need to integrate this into wider system so that it also marks the rack as cleared
            return

        else:
            # 2. Find laser distance, fire once
            laser_distance = rec_dist_laser()
             
            # 3. Update the CURRENT slot
            if laser_distance < 100: 
                delivery["R_detected"] = True
                delivery["delivery_state"] = Delivery_States.pickup
                delivery["ready_for_unloading"] = False
                delivery["rack_state"] = Delivery_Rack_States.load_detected
                delivery["search_slot_counter"] += 1
                robot["mode"] = Mode.delivery
                return
            else:
                delivery["slot_status"][delivery["search_slot_counter"]] = 1
                delivery["search_slot_counter"] += 1
                #mark the slot as cleared
            return laser_distance
    
    else:
        return None
    
def detect_junction_type(SL, SR):
    if (SL == 1 and SR == 0): 
        return Junctions.L
    elif (SL == 0 and SR == 1):
        return Junctions.R
    elif (SL == 1 and SR == 1):
        return Junctions.RL
    return Junctions.nil
   
#This one need to test, its going backwards so idk if the the logic will be reversed.
def back_line_follow_step(S1, S2):
  base = 80
  corr = 20
  
  if (S1 == 0 and S2 == 1): # corrects left veer
    motor_r.Reverse(speed = corr) # speed ranges from 0 to 100 as defined
    motor_l.Reverse(speed = base)
  elif (S1 == 1 and S2 == 0): #corrects right veer
    motor_l.Reverse(speed = corr)
    motor_r.Reverse(speed = base)
  else: #centered 
    motor_r.Reverse(speed = base)
    motor_l.Reverse(speed = base)

    """ if delivery["rack_state"] == Delivery_Rack_States.load_detected:
        print("IN load_detected")
 
        if robot["motion"] == Motion.turning:
            print("STARTING TURN NOW")
            robot["turn_complete"] = timed_turn_step(robot, 1000)
            if robot["turn_complete"]:
                print("APPROACHING 1")
                delivery["rack_state"] = Delivery_Rack_States.approaching
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["motion"] = Motion.follow
                robot["turn_complete"] = False """

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
        if sensors["SR"] == 1 and not delivery["bay_latch"]: # if new_junction: (includes NOt doublecounting)
            delivery["drop_off_bay"] += 1
            delivery["bay_latch"] = True # Block further counting until we leave the line
            #print(f"Passing branch {drop_off_bay}")
        
        
        if sensors["SR"] == 0:
            delivery["bay_latch"] = False # Reset the latch once we are back on black

        if delivery["drop_off_bay"] == delivery["target_bay"] and robot["motion"] != Motion.turning:
            print("Target reached! Turning into bay")
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            robot["turn_dir"] = Turn_Direction.right

    # --- MODIFIED FOR TESTING W/O GRABBER ---
    elif delivery["unloading_state"] == Unloading_States.found_bay:
        if events["new_T"]: #arrived at box
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            #release() #release grabber
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

turn_complete = False
#first_done = False -- local variables no need to define
#second_done = False
turn_phase = 0 # 0 = first 90, 1 = second 90 for 180 turn
def turn_180(turn_dir, S1, S2, turn_state, turn_phase, motor_l, motor_r):
    if turn_phase == 0:
        turn_state, first_done = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
        if first_done: 
            turn_state = Turn_State.start
            turn_phase = 1

    elif turn_phase == 1:
        turn_state, second_done = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
        if second_done:
            turn_phase = 0
            turn_state = Turn_State.start
            return turn_state, True, turn_phase

    return turn_state, False, turn_phase
