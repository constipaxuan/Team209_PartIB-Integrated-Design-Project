from line_following import detect_junction_type, line_follow_step, detect_junction, turn
from locations import Location, Elevator, Direction, Path, Junctions
from behaviour import Mode
from lowerpurple_upper_orange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff

location = Location.start
direction = Direction.cw
mode = Mode.start

# Note that take_next_turn has been defined in both here and map_state
take_next_turn = False 

#take_next_turn is decided in decision code. 
def take_a_turn():
    if detect_junction() == True and take_next_turn == True:
        turn()
        return True
    return False

def mode_tracker():
    pass

def start_mode():
    pass

def search_mode():
    pass

def delivery_mode():
    pass