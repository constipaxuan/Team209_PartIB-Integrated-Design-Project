from line_following import detect_junction_type, line_follow_step, detect_junction
from locations import Location, Unloading_States, Direction, Path, Junctions
from behaviour import Mode
from lowerpurple_upper_orange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff

location = Location.start
unloading_states = Unloading_States.none
direction = Direction.cw
mode = Mode.start

def mode_tracker():
    pass

def start_mode():
    pass

def search_mode():
    pass

def delivery_mode():
    pass