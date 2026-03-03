from line_following import detect_junction_type, line_follow_step, detect_junction, turn
from locations import Location, Elevator, Direction, Path, Junctions
from behaviour import Mode
from lowerpurple_upper_orange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff
from test_motor import Motor
from utime import sleep

location = Location.start
direction = Direction.cw
mode = Mode.start

#shld be defined in main code
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 


# For testing purposes: make it turn at every junction (maybe R if RL detected?) Just to make sure our junction detection logic works.
#def take_a_turn(junction_event):
#    return junction_event

#def mode_tracker():
#    pass

#def start_mode():
#    pass

def search_mode():
    pass

def delivery_mode(S1, S2, SL, SR, location, junction_type, new_junction, resistor_color):
    base = 70
    # Enter delivery mode when laser detects a resistor load while bot is on a branch. 
    if location == Location.rack_orange_L:
        if new_junction:
            turn()
        #move forward until you grab. After grabbing reverse until reach RL junction, turn 90 deg right (cw)
        direction = Direction.acw
        #rack_branches_OL is known
        while memory["rack_branches_OL"] % 6 != 0:
            if junction_type == Junctions.L:
                memory["rack_branches_OL"] -= 1
        LHS_dropoff(resistor_color)
        #enter unloading bay with blue closest
        # LHS dropoff stops when load has been deposited
        # reverse until reach RL junction. turning direction depends on where u wanna go next -- handled by search decision?
        motor_l.Forward(base)
        motor_r.Forward(base)
        sleep(0.5)
        while junction_type != Junctions.RL:
            # exit this loop when T junction is detected.
            line_follow_step(S1, S2)
        #decide to turn left or right depending on which rack it wants to go to.
    
    elif location == Location.rack_purple_L:
