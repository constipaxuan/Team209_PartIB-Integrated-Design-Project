from line_following import detect_junction_type, line_follow_step, detect_junction, turn
from locations import Location, Elevator, Direction, Path, Junctions
from behaviour import Mode

location = Location.start
direction = Direction.cw
mode = Mode.start



# For testing purposes: make it turn at every junction (maybe R if RL detected?) Just to make sure our junction detection logic works.
def take_a_turn(junction_event):
    return junction_event

def mode_tracker():
    pass

def start_mode():
    pass

def search_mode():
    pass

def delivery_mode():
    pass