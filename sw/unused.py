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
turn_phase = 0 # 0 = first 82, 1 = second 82 for 180 turn
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

# -- LOOP + MAPPING TEST ---
while True:
    sensors["S1"] = S1_sensor.value()
    sensors["S2"] = S2_sensor.value()
    sensors["SL"] = SL_sensor.value()
    sensors["SR"] = SR_sensor.value()

    
    button_now = button.value()

    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)            # specifically T-shape / both side sensors active
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]

    # non blocking debouncing. this allows sensors to still be read while button is being debounced, preventing missed junctions.
    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()
    
    prev_button = button_now 
    
    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]
        continue
        
    elif ON:

        #if events["new_junction"] and robot["motion"] == Motion.follow:
        #    if robot["direction"] == Direction.acw:
        #        robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] + 1) % N
        #    if robot["direction"] == Direction.cw:
        #        robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] - 1) % N

        if robot["mode"] == Mode.start:
            get_out_of_box(sensors, events, robot, delivery)

        elif robot["mode"] == Mode.search_init:
            # keep following until fully clear of any startup junction/T
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            if not events["on_junction"] and not events["on_T"]:
                robot["motion"] = Motion.follow
                robot["tnt_state"] = TNT_states.nil
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                events["prev_on_junction"] = False
                events["prev_on_T"] = False
                robot["mode"] = Mode.search

        
        else:
            if robot["tnt_state"] == TNT_states.nil:
                test_corner, OB_counter = test_main_loop(robot, events, test_corner, OB_counter)

            if robot["motion"] == Motion.follow:
                if robot["tnt_state"] == TNT_states.TNT:
                    if not events["on_junction"]:
                        robot["tnt_state"] = TNT_states.waiting
                        print("waiting")
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)


                elif robot["tnt_state"] == TNT_states.waiting:
                    if events["new_junction"]:
                        robot["tnt_state"] = TNT_states.NT_is_here
                        print("NT")
                        Red.value(0)
                        Green.value(0)
                        Yellow.value(0)
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

                
                elif robot["tnt_state"] == TNT_states.NT_is_here:
                    sensors["SL"] = SL_sensor.value()
                    sensors["SR"] = SR_sensor.value()
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    robot["motion"] = Motion.turning
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
                    Red.value(1)

                else:
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            elif robot["motion"] == Motion.turning:
                if not robot["turn_complete"]:
                    robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)

                else:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["tnt_state"] = TNT_states.nil
                    print(f"location:", robot["location"])
                    Red.value(0)
                    Green.value(0)
                    Yellow.value(0)
                    if corner_idx < len(corners) - 1:
                        corner_idx += 1
                    else:
                        corner_idx = 0
                        if events["on_T"]:
                            motor_l.Forward(speed = 0)
                            motor_r.Forward(speed = 0)
                        else:
                            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
                    
                    test_corner = corners[corner_idx]
                    
    
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]

        def test_main_loop(robot, events, test_corner, OB_counter):
    if test_corner == Test_Corners.upper_right:
        if events["new_T"]:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            Red.value(1)
    if test_corner == Test_Corners.upper_left:
        if events["new_junction"]:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            Green.value(1)
    if test_corner == Test_Corners.unloading:
        if OB_counter == 6:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            OB_counter = 0
            Yellow.value(1)
        else:
            if events["new_T"]:
                OB_counter = 0
            elif events["new_junction"]:
                OB_counter += 1
            robot["tnt_state"] = TNT_states.nil
    if test_corner == Test_Corners.back_to_start:
        if events["new_junction"]:
            robot["tnt_state"] = TNT_states.TNT
            robot["turn_dir"] = Turn_Direction.right
    
    return test_corner, OB_counter

def rack_search(sensors, events, robot, delivery):
    if robot["motion"] == Motion.follow:
            if events["new_junction"]:
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                robot["motion"] = Motion.stopped_for_scan
                robot["scan_start"] = ticks_ms()
            else:
                line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        

    elif robot["motion"] == Motion.stopped_for_scan:
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)

        if ticks_diff(ticks_ms(), robot["scan_start"]) >= 30: # edit
            if target_racks[robot["target_rack_idx"]] == Racks.rack_purple_L or target_racks[robot["target_rack_idx"]] == Racks.rack_orange_U:
                laser_distance = rec_dist_laserL()
            elif target_racks[robot["target_rack_idx"]] == Racks.rack_purple_U or target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L:
                laser_distance = rec_dist_laserR()
            print("NEW distance:", laser_distance)
            print("slot counter:", delivery["search_slot_counter"])
            print("slot status:", delivery["slot_status"])

            if laser_distance < 100:
                Red.value(1)
                delivery["R_detected"] = True
                delivery["delivery_state"] = Delivery_States.pickup
                delivery["ready_for_unloading"] = False
                delivery["rack_state"] = Delivery_Rack_States.approaching
                delivery["search_slot_counter"] += 1

                robot["turn_complete"] = False
                robot["timed_turn_started"] = False
                robot["motion"] = Motion.turning

                if robot["direction"] == Direction.cw:
                    robot["turn_dir"] = Turn_Direction.right
                elif robot["direction"] == Direction.acw:
                    robot["turn_dir"] = Turn_Direction.left
                
                return

            else:
                delivery["slot_status"][delivery["search_slot_counter"]] = 1
                robot["motion"] = Motion.follow

                if delivery["search_slot_counter"] < 5: #changed 6 to 5
                    delivery["search_slot_counter"] += 1
                else:
                    delivery["search_slot_counter"] = 0
                    robot["motion"] = Motion.follow
                    delivery["rack_cleared"] = True
                    robot["target_rack_idx"] = (robot["target_rack_idx"] + 1) % 4
                    delivery["slot_status"] = [0,0,0,0,0,0]
                    robot["motion"] = Motion.follow
                    return
    
    elif robot["motion"] == Motion.turning:
        robot["turn_complete"] = timed_turn_step(robot, 1000)
        if robot["turn_complete"] == True:
            robot["mode"] = Mode.delivery
            robot["motion"] = Motion.follow 
            robot["gnd_loc_idx"] = 0 # reinitialising it bc bot is unable to orient itself atp.              
            return

# --- Keep as it is ---
def handler_orange_L_delivery(sensors, events, robot, delivery):
    # Step 1: Enter delivery mode when laser has turned into branch. 
        
    if delivery["rack_state"] == Delivery_Rack_States.approaching:
        #print("APPROACHING 2")
        if not delivery["timed_rev_started"]:
                delivery["timed_rev_started"] = True
                delivery["timed_rev_start"] = ticks_ms()

        else:
            #print("FOLLOW")
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            if ticks_diff(ticks_ms(), delivery["timed_rev_start"]) > 700:   # modify according to needs.
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                delivery["timed_rev_started"] = False
                delivery["rack_state"] = Delivery_Rack_States.reached
                Red.value(0)
          
    
    # MODIFIED FOR TESTING
    # Step 3: Grab the load. Adjust timing in R_measure so that the claw can shut before the bot starts reversing. atp IDGAF is this part is blocking.
    elif delivery["rack_state"] == Delivery_Rack_States.reached:
        sleep_ms(400) 
        delivery["resistor_color"] = Resistor_Color.green #measure the resistor color and store it as a variable so that the bot knows which bay to drop it off at
        delivery["rack_state"] = Delivery_Rack_States.reorienting
        robot["motion"] = Motion.turning
        robot["turn_dir"] = Turn_Direction.right # Face the unloading bay.
        robot["timed_turn_started"] = False
    
    # Step 4: Reverse and turn towards unloading.

    elif delivery["rack_state"] == Delivery_Rack_States.reorienting:
        if delivery["getout_state"] == Get_Out_of_branch.Rev_Branch:
            if not delivery["timed_rev_started"]:
                delivery["timed_rev_started"] = True
                delivery["timed_rev_start"] = ticks_ms()

            else:
                motor_l.Reverse(speed=80)
                motor_r.Reverse(speed=80)

            if ticks_diff(ticks_ms(), delivery["timed_rev_start"]) > 1200:   # modify according to needs.
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                robot["motion"] = Motion.follow
                delivery["timed_rev_started"] = False
                delivery["getout_state"] = Get_Out_of_branch.Exiting_Branch

        elif delivery["getout_state"] == Get_Out_of_branch.Exiting_Branch:
            if robot["motion"] != Motion.turning:
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                Blue.value(1)
                print("start timed turn!")
            
            if robot["motion"] == Motion.turning:
                robot["turn_complete"] = timed_turn_step(robot, 1200)
                if robot["turn_complete"]:
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
                    Blue.value(0)
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    delivery["getout_state"] = Get_Out_of_branch.RackZone
                    print("timed turn finished")
                    delivery["last_branch_time"] = ticks_ms()

        # On the straight, need to get out of rack zone.
        elif delivery["getout_state"] == Get_Out_of_branch.RackZone:
            if events["new_junction"]:
                delivery["last_branch_time"] = ticks_ms()

            if ticks_diff(ticks_ms(), delivery["last_branch_time"]) > 2500:
                print("out of rack zone")
                delivery["getout_state"] = Get_Out_of_branch.Rev_Branch #reset
                delivery["rack_state"] = Delivery_Rack_States.load_detected #reset to search for next load after passing each branch, since each bay has 6 branches.
                delivery["ready_for_unloading"] = True
                robot["gnd_loc_idx"] = 19 #OL6
            
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

def LHS_dropoff(sensors, events, robot, delivery):
    # ASSIGNING TARGET BAY
    if delivery["resistor_color"] == Resistor_Color.red: 
        delivery["target_bay"] = 2 # Red, which is the rightmost bay
    elif delivery["resistor_color"] == Resistor_Color.yellow: 
        delivery["target_bay"] = 1 # Yellow
    elif delivery["resistor_color"] == Resistor_Color.green: 
        delivery["target_bay"] = 21 # Green, skip 1 to skip the starting box
    elif delivery["resistor_color"] == Resistor_Color.blue: 
        delivery["target_bay"] = 20 # Blue 


    # State machine 
    if delivery["unloading_state"] == Unloading_States.finding_bay:
            
        # TARGET DETECTION  
        # case when the target bay is blue, no need to turn -- blue bay is literally straight ahead. 
        if delivery["resistor_color"] == Resistor_Color.blue:
            if robot["gnd_loc_idx"] == 20: # blue bay node.
                delivery["unloading_state"] = Unloading_States.found_bay
                
        else:
        # Turning into unloading corridoor if target bay is not blue. Motion = turning when correct bay is found. Handled in decision loop.
            if robot["gnd_loc_idx"] == 20 and robot["motion"] != Motion.turning:
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
                robot["turn_dir"] = Turn_Direction.left
                    
    elif delivery["resistor_color"] != Resistor_Color.blue and delivery["unloading_state"] == Unloading_States.counting_bays:

        if robot["gnd_loc_idx"] == delivery["target_bay"] and robot["motion"] != Motion.turning:
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

def delivery_from_orange_L(sensors, events, robot, delivery):
    if delivery["delivery_state"] == Delivery_States.pickup:
        if delivery["ready_for_unloading"] == False:
            handler_orange_L_delivery(sensors, events, robot, delivery)
        elif delivery["ready_for_unloading"] == True:
            delivery["ready_for_unloading"] = False #reset for next load
            delivery["delivery_state"] = Delivery_States.unloading
        
    elif delivery["delivery_state"] == Delivery_States.unloading:
        LHS_dropoff(sensors, events, robot, delivery) 
        if delivery["unloading_state"] == Unloading_States.done:
            delivery["delivery_state"] = Delivery_States.recover
            delivery["unloading_state"] = Unloading_States.finding_bay
    
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
            handler_blue_bay(sensors, events, robot, delivery) # becomes mode search after this func ends.

def update_start_T_count(start_T_shape_count, new_T):
    #global start_T_shape_count, counting
    if new_T:
        start_T_shape_count += 1
    print(f"T shapes passed: {start_T_shape_count}")
    return start_T_shape_count

# Call this in discrete time steps while mode = Mode.start
def get_out_of_box(sensors, events, robot, delivery):
    # --- Main Mission Loop ---

    # start_T_shape_count is only used for getting out of box, after that on main loop use gnd_loc_idx.
    if robot["start_state"] == Start_States.start:
        events["start_T_shape_count"] = update_start_T_count(events["start_T_shape_count"], events["new_T"])

    if robot["start_state"] == Start_States.start:   
    # State 1: Drive out of the box, drive straight
    #if start_T_shape_count < 2:
        if events["start_T_shape_count"] == 2:
            #if sensors["SL"] == 0 and sensors["SR"] == 0: # Move forward until the SL and SR lose the white line. 
            Blue.value(1)
            robot["start_state"] = Start_States.turn1
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_state"] = Turn_State.start
            robot["turn_complete"] = False
            robot["gnd_loc_idx"] = 0 # set to 0
            robot["motion"] = Motion.turning

        else:
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    # State 2: Hit second T shape, turn clockwise
    elif robot["start_state"] == Start_States.turn1:

        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if  robot["turn_complete"]:
            robot["start_state"] = Start_States.turn1_done
            robot["motion"] = Motion.follow
            Blue.value(0)
            #print("turn 1 done")
    
    elif robot["start_state"] == Start_States.turn1_done:
        if robot["gnd_loc_idx"] == 2: #red bay
            robot["start_state"] = Start_States.turn2
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            robot["motion"] = Motion.turning
            Blue.value(1)

        else:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    elif robot["start_state"] == Start_States.turn2:
        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if robot["turn_complete"]:
            #print("turn 2 COMPLETED")
            robot["start_state"] = Start_States.turn2_done
            delivery["target_rack"] = Location.rack_purple_L
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            robot["motion"] = Motion.follow
            Blue.value(0)
            
            
    
    elif robot["start_state"] == Start_States.turn2_done:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        robot["mode"] = Mode.search_init
        #print("turn 2 done")

# returns True when turn complete, False otherwise. Call in discrete time steps while in turning mode.
# change speed of wheel to match position of ideal pivot (lies on 45 degree line from the corner)
# Prevents original line from being misidentified as the new line by forcing bot to lose the first line before finding the new one.
def turn_v4(robot, sensors):
    if robot["turn_state"] == Turn_State.start:
        if (sensors["S1"] == 0 and sensors["S2"] == 0): # Lost the original line
            robot["turn_state"] = Turn_State.line_lost

    
    elif robot["turn_state"] == Turn_State.line_lost:
        if (sensors["S1"] == 1 and sensors["S2"] == 1): # Found the new line. 
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_state"] = Turn_State.start
            return True
        
    if robot["turn_dir"] == Turn_Direction.left:
        motor_l.Forward(speed = 60)
        motor_r.Forward(speed = 20)

    elif robot["turn_dir"] == Turn_Direction.right:
        motor_l.Forward(speed = 20)
        motor_r.Forward(speed = 60)
    
    return False
    
# robot["turn_complete"] = turn_v4(robot, sensors)

# robot["turn_complete"] = timed_turn_step(robot, time_ms)