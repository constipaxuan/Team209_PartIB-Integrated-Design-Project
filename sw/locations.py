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
    RorL = 1
    RL = 2
    nil = 3

class Target_Rack:
    orange_L = 1
    purple_L = 2
    orange_U = 3
    purple_U = 4