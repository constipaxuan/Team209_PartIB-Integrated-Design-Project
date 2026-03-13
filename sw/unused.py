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