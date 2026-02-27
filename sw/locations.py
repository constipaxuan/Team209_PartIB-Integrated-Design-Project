from enum import Enum

class Path(Enum):
    line = 1
    junction = 2

class Location(Enum):
    start = 0
    unloading = 1
    elevator_low = 2
    rack_orange_L = 3
    rack_purple_L = 4
    rack_orange_U = 5
    rack_purple_U = 6
    elevator = 7
    elevator_up = 8

class Elevator(Enum):
    none = 0
    low = 1
    high = 2
    
class Direction(Enum):
    cw = 1
    acw = 2

class Junctions(Enum):
    R = 1
    L = 2
    RL = 3
    nil = 4