#from enum import Enum

class Action:
    follow = 1
    turning = 2

class Location:
    start = 0
    unloading = 1
    elevator_low = 2
    rack_orange_L = 3
    rack_purple_L = 4
    rack_orange_U = 5
    rack_purple_U = 6
    elevator_up = 7

class Resistor_Color:
    none = 0
    red = 1
    yellow = 2
    green = 3
    blue = 4
    
class Direction:
    cw = 1
    acw = 2

class Junctions:
    R = 1
    L = 2
    RL = 3
    nil = 4
