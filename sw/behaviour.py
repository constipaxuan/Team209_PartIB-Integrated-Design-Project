#from enum import Enum

class Mode:
    start = 0
    search_init = 1
    search = 2
    delivery = 3

class Turn_Direction:
    left = 0
    right = 1
    nil = 2
    half = 3

class Turn_State:
    start = 0
    overshot = 1
    line_lost = 2
    done = 3

class Start_States:
    start = 0
    turn1 = 1 # turn RIGHT
    turn2 = 2 # turn LEFT
    turn1_done = 3
    turn2_done = 4

class Delivery_Rack_States:
    approaching = 1
    reached = 2
    reorienting = 3
    done = 4
    
class Unloading_States:
    finding_bay = 0
    counting_bays = 1
    found_bay = 2
    done = 3

class Delivery_States:
    pickup = 0
    unloading = 1
    recover = 2

class TNT_states:
    nil = 0
    TNT = 1
    waiting = 2
    NT_is_here = 3




