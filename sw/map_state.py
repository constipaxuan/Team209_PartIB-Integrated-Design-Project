#this code is NOT functional. Handling logic right now but eventiually it WILL be pipelined and not stuck in this monstrosity of blocking while loops.
from line_following import detect_junction_type, line_follow_step, detect_junction
from locations import Location, Elevator, Direction, Path, Junctions
from behaviour import Mode
from decision import take_a_turn
from machine import Pin

location = Location.start
direction = Direction.cw
mode = Mode.start


path = Path.line
upstairs = False



#need to map pins
S1_pin = 10
S2_pin = 11 
SL_pin = 
SR_pin =

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

SL = SL_sensor.value()
SR = SR_sensor.value()

# Memory variables -- we want to store values across time steps.
prev_on_junction = False
rack_branches_OL = 0
rack_branches_PL = 0
rack_branches_OH = 0
rack_branches_PH = 0
elevator_low_branches = 0
elevator_high_branches = 0
take_next_turn = False # decide whether to take the turn.
prev_elevator_state = None

#Main forever loop
#while True:
    
    #AT the end of the loop. Memory stored for next cycle. 
#    prev_on_junction = (SL == 1 or SR == 1)

#DONT implement behaviour at all. JUST TRACK LOCATIONS GODDAMN
# Broken down into 3 modes.
def mapping(previous_state, SL, SR, mode, direction):
    #Only call once per cycle. 
    junction_event = detect_junction(prev_on_junction, SL_sensor, SR_sensor)
    if junction_event:
        junction_type = detect_junction_type(prev_on_junction, path, SL_sensor, SR_sensor)
    else:
        junction_type = Junctions.nil
    if mode == Mode.start():
            return Location.start
    if mode == Mode.search():
        if previous_state == Location.unloading:
        # once it detects the RL (T) junction at the end it knows it has reached the end of the unloading bay. 
        # Only applies when the robot is already in search mode. If it is in delivery mode it will be coming out of a branch and will detect a RL within unloading area.
            if junction_type == Junctions.RL:
                if direction == Direction.cw:
                    return Location.rack_orange_L
                elif direction == Direction.acw:
                    return Location.rack_purple_L
            return Location.unloading
        
        elif previous_state == Location.rack_orange_L:
            if direction == Direction.cw:
                if junction_type == Junctions.RL:
                    rack_branches_OL = 0
                    prev_elevator_state = Elevator.none
                    return Location.elevator_low
                elif junction_type == Junctions.R:
                    rack_branches_OL += 1
                return Location.rack_orange_L
            if direction == Direction.acw:
                if junction_type == Junctions.L:
                    rack_branches_OL -= 1
                if rack_branches_OL == -6:
                    rack_branches_OL = 0
                    return Location.unloading()
                return Location.rack_orange_L

        elif previous_state == Location.rack_purple_L:
            if direction == Direction.acw:
                if junction_type == Junctions.RL:
                    rack_branches_PL = 0
                    prev_elevator_state = Elevator.none
                    return Location.elevator_low
                elif junction_type == Junctions.L:
                    rack_branches_PL += 1
                return Location.rack_purple_L
            if direction == Direction.cw:
                if junction_type == Junctions.R:
                    rack_branches_PL -= 1
                if rack_branches_PL == -6:
                    rack_branches_PL = 0
                    return Location.unloading()
                return Location.rack_purple_L
            
        elif previous_state == Location.elevator_low:
            if prev_elevator_state == Elevator.none:
                if direction == Direction.cw:
                    if junction_type == Junctions.R:
                        elevator_low_branches += 1
                        if abs(elevator_low_branches) == 2 and take_a_turn() == True:
                            elevator_low_branches = 0
                            prev_elevator_state = Elevator.low
                            return Location.elevator
                    elif junction_type == Junctions.RL:
                        elevator_low_branches = 0
                        return Location.rack_purple_L
                    return Location.elevator_low
                if direction == Direction.acw:
                    if junction_type == Junctions.L:
                        elevator_low_branches -= 1
                        if abs(elevator_low_branches) == 2 and take_a_turn() == True:
                            elevator_low_branches = 0
                            prev_elevator_state = Elevator.low
                            return Location.elevator
                    elif junction_type == Junctions.RL:
                        elevator_low_branches = 0
                        return Location.rack_orange_L
            else:
                if junction_type == (Junctions.R or Junctions.L):
                    #I am writing this on the assumption that once the bot reaches the lower floor T it will NOt suddenly turn 180 and go back up because it makes no sense.
                    #I have also assumed that the prev_on_junction thing will avoid double counting the same T junction after rotation.
                    prev_elevator_state == Elevator.none
            return Location.elevator_low
            
        elif previous_state == Location.elevator:
            if junction_type == Junctions.RL:
                if prev_elevator_state == Elevator.low:
                    # I dont know whether the T junction right after turn will trigger this condition as well.
                    prev_elevator_state = Elevator.high
                    return Location.elevator_up
                elif prev_elevator_state == Elevator.high:
                    prev_elevator_state = Elevator.low
                    return Location.elevator_low
            return Location.elevator

        elif previous_state == Location.elevator_up:
            if prev_elevator_state == Elevator.none:
                if direction == Direction.cw:
                    if junction_type == Junctions.R:
                        elevator_high_branches += 1
                        if abs(elevator_high_branches) == 2 and take_a_turn() == True:
                            elevator_high_branches = 0
                            prev_elevator_state = Elevator.high
                            return Location.elevator
                    elif junction_type == Junctions.L:
                        elevator_high_branches = 0
                        return Location.rack_orange_U
                    return Location.elevator_up
                if direction == Direction.acw:
                    if junction_type == Junctions.L:
                        elevator_high_branches -= 1
                        if abs(elevator_high_branches) == 2 and take_a_turn() == True:
                            elevator_high_branches = 0
                            prev_elevator_state = Elevator.high
                            return Location.elevator
                    elif junction_type == Junctions.R:
                        elevator_low_branches = 0
                        return Location.rack_purple_U
            else:
                if junction_type == (Junctions.R or Junctions.L):
                    #I am writing this on the assumption that once the bot reaches the floor T it will NOt suddenly turn 180 and go back up because it makes no sense.
                    prev_elevator_state == Elevator.none
            return Location.elevator_up

        elif previous_state == Location.rack_orange_U:
            pass
        elif previous_state == Location.rack_purple_U:
            pass

    if mode == Mode.delivery():
        pass

#direction = rotation_tracker()
#mode = mode_tracker()
#location = mapping(location, SL, SR, mode, direction)

branch_count = 0
unloading_state = 0 #check if this is acceptable. Zero again once outside unloading zone.
def unloading_zone(SL, SR):
    if mode == Mode.search or mode == Mode.delivery:
        if (branch_count == 0 and SR == 1):
            unloading_state = Unloading_States.red
            branch_count += 1
        elif (branch_count == 1 and SR == 1):
            unloading_state = Unloading_States.yellow
            branch_count += 1
        elif (branch_count == 2 and SR == 1):
            unloading_state = Unloading_States.none
            branch_count += 1
        elif (branch_count == 3 and SR == 1):
            unloading_state = Unloading_States.green
            branch_count += 1
        elif (branch_count == 4 and SR == 1):
            unloading_state = Unloading_States.blue
            branch_count += 1

        if (branch_count == 0 and SL == 1):
            unloading_state = Unloading_States.blue
            branch_count += 1
        elif (branch_count == 1 and SL == 1):
            unloading_state = Unloading_States.green
            branch_count += 1
        elif (branch_count == 2 and SL == 1):
            unloading_state = Unloading_States.none
            branch_count += 1
        elif (branch_count == 3 and SL == 1):
            unloading_state = Unloading_States.yellow
            branch_count += 1
        elif (branch_count == 4 and SL == 1):
            unloading_state = Unloading_States.red
            branch_count += 1
        elif branch_count == 5 and rotate

def rack_zone():
    if direction == Direction.cw:




while True:
    #read sensors here
    #SL = 
    #SR = 
    while (in_elevator == False and upstairs == False): # while downstairs
        if (SL and SR == True): #encountered + shape
            cross = True
            while (SL ^ SR == False): #+ or line. Need to check whether it instantly deactivates upon running into L or R junctions.
                if SL == True:
                    cross = False
                    acw = True
                    cw = False
                    unloading_zone = False
                elif SR == True:
                    cross = False
                    acw = False
                    cw = True
                    unloading_zone = False
    
        while cw:
            # The below code handles enter and exit of the lower elevator zone.
            if (orange_rack == True and cross == True) :
                orange_rack = False
                elevator_low = True
            elif (elevator_low == True and cross == True): #need to define elevator function
                purple_rack = True
                elevator_low = False
        
            while purple_rack == True: # potential issues: 6th branch not recognised, considered unloading zone. 
                #Currently the solution to that is that under a while True loop we will have if purple_rack then call the rack function that runs until 6 branches r cleared. 
                #Bot will enter and exit multiple times though, need to make sure function doesn't get called more than once. Can add a running variable that stops that.
                while rack_branch_count < 6:
                    if (SR ^ SL == True): # by right it is SR = True
                        rack_branch_count += 1
                rack_branch_count = 0
                unloading_zone = True
                purple_rack = False
            
        
            #fill in later
            while orange_rack:
                pass
            
            while unloading_zone:
                #Red Yellow Green Blue






        while acw:
            # The below code handles enter and exit of the lower elevator zone.
            if (elevator_low == True and cross == True):
                orange_rack = True
                elevator_low = False
            elif (purple_rack == True and cross == True):
                elevator_low = True
                purple_rack = False
            
            while orange_rack == True:
                while rack_branch_count < 6:
                    if (SR ^ SL == True): # by right it is SL = True
                        rack_branch_count += 1
                rack_branch_count = 0
                unloading_zone = True
                orange_rack = False
            
            #fill in later
            while purple_rack:
                pass


       




         
