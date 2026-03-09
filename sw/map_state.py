#this code is NOT functional. Handling logic right now but eventiually it WILL be pipelined and not stuck in this monstrosity of blocking while loops.
from line_following import detect_junction_type, line_follow_step, detect_junction
from locations import Location, Elevator, Direction, Path, Junctions
from behaviour import Mode, Turn_Direction
from decision import take_a_turn
from machine import Pin

#initialise - will be moved to main code later. 
location = Location.start
direction = Direction.cw
mode = Mode.start





#need to map pins
S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

SL = SL_sensor.value()
SR = SR_sensor.value()

# Memory variables -- we want to store values across time steps. Will be moved to main code.

memory = {
    "prev_on_junction" : False,
    "rack_branches_OL" : 0,
    "rack_branches_PL" : 0,
    "rack_branches_OH" : 0,
    "rack_branches_PH" : 0,
    "elevator_low_branches" : 0,
    "elevator_high_branches" : 0,
}

#Will be moved to main code
def init_memory():
    return {
        "prev_on_junction": False,
        "rack_branches_OL": 0,
        "rack_branches_PL": 0,
        "rack_branches_OH": 0,
        "rack_branches_PH": 0,
        "elevator_low_branches": 0,
        "elevator_high_branches": 0,
    }

#Main forever loop
#while True:
    
    #AT the end of the loop. Memory stored for next cycle. 
#    prev_on_junction = (SL == 1 or SR == 1)

#include in main while loop 
on_junction = (SL == 1 or SR == 1)
new_junction = (not memory["prev_on_junction"] and on_junction)

if new_junction:
    junction_type = detect_junction_type(memory["prev_on_junction"], SL_sensor, SR_sensor)
else:
    junction_type = Junctions.nil
# end

#replace take_a_turn with take_next_turn
def mapping(previous_state, mode, direction, junction_type):
    #Only call once per cycle. 

    if mode == Mode.start:
            return Location.start
    if mode == Mode.search:
        key = (mode, previous_state, direction, junction_type)
        if key in SEARCH_TRANSITIONS:
            next_state = SEARCH_TRANSITIONS[key]()
            return next_state
        return previous_state
    if mode == Mode.delivery:
        pass

#direction = rotation_tracker()
#mode = mode_tracker()
#location = mapping(location, SL, SR, mode, direction)

# State transition table : keys are (mode, previous_location, direction, junction_type). Values are location
# For search mode. output is location and location only. No decision making involved.
SEARCH_TRANSITIONS = {
    #start mode: only one state so no transitions needed.
    
    #unloading 
    (Mode.search, Location.unloading, Direction.cw, Junctions.RL): lambda :Location.rack_orange_L,
    (Mode.search, Location.unloading, Direction.acw, Junctions.RL): Location.rack_purple_L,

    #rack_orange_L
    (Mode.search, Location.rack_orange_L, Direction.cw, Junctions.RL): lambda : handler_rack_orange_L(Direction.cw, Junctions.RL),
    (Mode.search, Location.rack_orange_L, Direction.cw, Junctions.R): lambda : handler_rack_orange_L(Direction.cw, Junctions.R),
    (Mode.search, Location.rack_orange_L, Direction.acw, Junctions.L): lambda : handler_rack_orange_L(Direction.acw, Junctions.L),

    #rack_purple_L
    (Mode.search, Location.rack_purple_L, Direction.acw, Junctions.RL): lambda : handler_rack_purple_L(Direction.acw, Junctions.RL),
    (Mode.search, Location.rack_purple_L, Direction.acw, Junctions.L): lambda : handler_rack_purple_L(Direction.acw, Junctions.L),
    (Mode.search, Location.rack_purple_L, Direction.cw, Junctions.R): lambda : handler_rack_purple_L(Direction.cw, Junctions.R),

    #elevator_low
    (Mode.search, Location.elevator_low, Direction.cw, Junctions.R): lambda : handler_elevator_low(Direction.cw, Junctions.R),
    (Mode.search, Location.elevator_low, Direction.cw, Junctions.RL): lambda : handler_elevator_low(Direction.cw, Junctions.RL),
    (Mode.search, Location.elevator_low, Direction.acw, Junctions.L): lambda : handler_elevator_low(Direction.acw, Junctions.L),
    (Mode.search, Location.elevator_low, Direction.acw, Junctions.RL): lambda : handler_elevator_low(Direction.acw, Junctions.RL),

    #elevator_up
    (Mode.search, Location.elevator_up, Direction.cw, Junctions.R): lambda : handler_elevator_up(Direction.cw, Junctions.R),
    (Mode.search, Location.elevator_up, Direction.cw, Junctions.L): lambda : handler_elevator_up(Direction.cw, Junctions.L),
    (Mode.search, Location.elevator_up, Direction.cw, Junctions.RL): lambda : handler_elevator_up(Direction.cw, Junctions.RL),
    (Mode.search, Location.elevator_up, Direction.acw, Junctions.L): lambda : handler_elevator_up(Direction.acw, Junctions.L),
    (Mode.search, Location.elevator_up, Direction.acw, Junctions.R): lambda : handler_elevator_up(Direction.acw, Junctions.R),
    (Mode.search, Location.elevator_up, Direction.acw, Junctions.RL): lambda : handler_elevator_up(Direction.acw, Junctions.RL),

    #rack_orange_U
    (Mode.search, Location.rack_orange_U, Direction.acw, Junctions.L): lambda : handler_rack_orange_U(Direction.acw, Junctions.L),

    #rack_purple_U
    (Mode.search, Location.rack_purple_U, Direction.cw, Junctions.R): lambda : handler_rack_purple_U(Direction.cw, Junctions.R)
}

#Local rack handlers
def handler_rack_orange_L(direction, junction_type):
    if direction == Direction.cw:
        if junction_type == Junctions.RL:
            memory["rack_branches_OL"] = 0
            #memory["prev_elevator_state"] = Elevator.none
            return Location.elevator_low
        elif junction_type == Junctions.R:
            memory["rack_branches_OL"] += 1
            return Location.rack_orange_L
        
    if direction == Direction.acw:
        if junction_type == Junctions.L:
            memory["rack_branches_OL"] -= 1
        if memory["rack_branches_OL"] == -6:
            memory["rack_branches_OL"] = 0
            return Location.unloading
    return Location.rack_orange_L

def handler_rack_purple_L(direction, junction_type):
    if direction == Direction.acw:
        if junction_type == Junctions.RL:
            memory["rack_branches_PL"] = 0
            #memory["prev_elevator_state"] = Elevator.none
            return Location.elevator_low
        elif junction_type == Junctions.L:
            memory["rack_branches_PL"] += 1
            return Location.rack_purple_L
    if direction == Direction.cw:
        if junction_type == Junctions.R:
            memory["rack_branches_PL"] -= 1
            if memory["rack_branches_PL"] == -6:
                memory["rack_branches_PL"] = 0
                return Location.unloading()
    return Location.rack_purple_L

def handler_elevator_low(direction, junction_type):
        if direction == Direction.cw:
            # This occurs when the bot did take a turn to go up the elevator, so the next junction it sees is the T junction at the end of the elevator path.
            if abs(memory["elevator_low_branches"]) == 2 and junction_type == Junctions.RL:
                memory["elevator_low_branches"] = 0
                return Location.elevator_up
            
            elif junction_type == Junctions.R:
                memory["elevator_low_branches"] += 1
            
            elif junction_type == Junctions.RL:
                memory["elevator_low_branches"] = 0
                return Location.rack_purple_L

        if direction == Direction.acw:
            
            # assuming the bot doesnt make 180 turn in elevator because it makes no sense and is a waste of time.
            if abs(memory["elevator_low_branches"]) == 2 and junction_type == Junctions.RL:
                memory["elevator_low_branches"] = 0
                return Location.elevator_up
            
            elif junction_type == Junctions.L:
                memory["elevator_low_branches"] -= 1

            elif junction_type == Junctions.RL:
                memory["elevator_low_branches"] = 0
                return Location.rack_orange_L
            
        return Location.elevator_low

def handler_elevator_up(direction, junction_type):
    if direction == Direction.cw:
        if abs(memory["elevator_high_branches"]) == 2 and junction_type == Junctions.RL:
            memory["elevator_high_branches"] = 0
            return Location.elevator_low
        
        elif junction_type == Junctions.R:
            memory["elevator_high_branches"] += 1
        
        # crossed first branch of orange upper rack.
        elif junction_type == Junctions.L:
            memory["elevator_high_branches"] = 0
            return Location.rack_orange_U
    
    if direction == Direction.acw:
        if abs(memory["elevator_high_branches"]) == 2 and junction_type == Junctions.RL:
            memory["elevator_high_branches"] = 0
            return Location.elevator_low
        
        elif junction_type == Junctions.L:
                memory["elevator_high_branches"] -= 1
        
        # crossed first branch of purple upper rack.
        elif junction_type == Junctions.R:
            memory["elevator_high_branches"] = 0
            return Location.rack_purple_U

    return Location.elevator_up

def handler_rack_orange_U(direction, junction_type):
    if direction == Direction.acw:
        if junction_type == Junctions.L:
        # Again this is assuming logical decision making and the bot wont randomly turn 180 deg and go back into rack area once its coming back out.
            return Location.elevator_up
    return Location.rack_orange_U

def handler_rack_purple_U(direction, junction_type):
    if direction == Direction.cw:
        if junction_type == Junctions.R:
            return Location.elevator_up
    return Location.rack_purple_U

# Direction tracker - Call when turning. Only call in search mode. Outputs the current direction of the bot (cw or acw).
def direction_tracker(previous_direction, turn_dir):
    if turn_dir == Turn_Direction.half:
        return Direction.cw if previous_direction == Direction.acw else Direction.acw
    else:
        return previous_direction

    

""" def mapping(previous_state, mode, direction, junction_type):
    #Only call once per cycle. 

    if mode == Mode.start:
            return Location.start
    if mode == Mode.search:
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
                    memory["rack_branches_OL"] = 0
                    memory["prev_elevator_state"] = Elevator.none
                    return Location.elevator_low
                elif junction_type == Junctions.R:
                    memory["rack_branches_OL"] += 1
                return Location.rack_orange_L
            if direction == Direction.acw:
                if junction_type == Junctions.L:
                    memory["rack_branches_OL"] -= 1
                if memory["rack_branches_OL"] == -6:
                    memory["rack_branches_OL"] = 0
                    return Location.unloading()
                return Location.rack_orange_L

        elif previous_state == Location.rack_purple_L:
            if direction == Direction.acw:
                if junction_type == Junctions.RL:
                    memory["rack_branches_PL"] = 0
                    memory["prev_elevator_state"] = Elevator.none
                    return Location.elevator_low
                elif junction_type == Junctions.L:
                    memory["rack_branches_PL"] += 1
                return Location.rack_purple_L
            if direction == Direction.cw:
                if junction_type == Junctions.R:
                    memory["rack_branches_PL"] -= 1
                if memory["rack_branches_PL"] == -6:
                    memory["rack_branches_PL"] = 0
                    return Location.unloading()
                return Location.rack_purple_L
            
        elif previous_state == Location.elevator_low:
            if memory["prev_elevator_state"] == Elevator.none:
                if direction == Direction.cw:
                    if junction_type == Junctions.R:
                        memory["elevator_low_branches"] += 1
                        if abs(memory["elevator_low_branches"]) == 2 and memory["take_next_turn"] == True:
                            memory["elevator_low_branches"] = 0
                            memory["prev_elevator_state"] = Elevator.low
                            return Location.elevator
                    elif junction_type == Junctions.RL:
                        memory["elevator_low_branches"] = 0
                        return Location.rack_purple_L
                    return Location.elevator_low
                if direction == Direction.acw:
                    if junction_type == Junctions.L:
                        memory["elevator_low_branches"] -= 1
                        if abs(memory["elevator_low_branches"]) == 2 and memory["take_next_turn"] == True:
                            memory["elevator_low_branches"] = 0
                            memory["prev_elevator_state"] = Elevator.low
                            return Location.elevator
                    elif junction_type == Junctions.RL:
                        memory["elevator_low_branches"] = 0
                        return Location.rack_orange_L
            else:
                if (junction_type == Junctions.R or junction_type == Junctions.L):
                    #I am writing this on the assumption that once the bot reaches the lower floor T it will NOt suddenly turn 180 and go back up because it makes no sense.
                    #I have also assumed that the prev_on_junction thing will avoid double counting the same T junction after rotation.
                    memory["prev_elevator_state"] = Elevator.none
            return Location.elevator_low
            
        elif previous_state == Location.elevator:
            if junction_type == Junctions.RL:
                if memory["prev_elevator_state"] == Elevator.low:
                    # I dont know whether the T junction right after turn will trigger this condition as well.
                    memory["prev_elevator_state"] = Elevator.high
                    return Location.elevator_up
                elif memory["prev_elevator_state"] == Elevator.high:
                    memory["prev_elevator_state"] = Elevator.low
                    return Location.elevator_low
            return Location.elevator

        elif previous_state == Location.elevator_up:
            if memory["prev_elevator_state"] == Elevator.none:
                if direction == Direction.cw:
                    if junction_type == Junctions.R:
                        memory["elevator_high_branches"] += 1
                        if abs(memory["elevator_high_branches"]) == 2 and take_a_turn() == True:
                            memory["elevator_high_branches"] = 0
                            memory["prev_elevator_state"] = Elevator.high
                            return Location.elevator
                    elif junction_type == Junctions.L:
                        memory["elevator_high_branches"] = 0
                        return Location.rack_orange_U
                    return Location.elevator_up
                if direction == Direction.acw:
                    if junction_type == Junctions.L:
                        memory["elevator_high_branches"] -= 1
                        if abs(memory["elevator_high_branches"]) == 2 and take_a_turn() == True:
                            memory["elevator_high_branches"] = 0
                            memory["prev_elevator_state"] = Elevator.high
                            return Location.elevator
                    elif junction_type == Junctions.R:
                        memory["elevator_high_branches"] = 0
                        return Location.rack_purple_U
            else:
                if junction_type == Junctions.R or junction_type == Junctions.L:
                    #I am writing this on the assumption that once the bot reaches the upper floor T it will NOt suddenly turn 180 and go back down because it makes no sense.
                    memory["prev_elevator_state"] = Elevator.none
            return Location.elevator_up

        elif previous_state == Location.rack_orange_U:
            if direction == Direction.acw:
                if junction_type == Junctions.L:
                # Again this is assuming logical decision making and the bot wont randomly turn 180 deg and go back into rack area once its coming back out.
                    return Location.elevator_up
            return Location.rack_orange_U
        elif previous_state == Location.rack_purple_U:
            if direction == Direction.cw:
                if junction_type == Junctions.R:
                    return Location.elevator_up
            return Location.rack_purple_U
        
    if mode == Mode.delivery:
        pass """