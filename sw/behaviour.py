#from enum import Enum

class Mode:
    start = 0
    search = 1
    delivery = 2

class Turn_Direction:
    left = 0
    right = 1
    nil = 2
    half = 3

class Turn_State:
    start = 0
    line_lost = 1
    done = 2

class Start_States:
    start = 0
    turn1 = 1 # turn RIGHT
    turn2 = 2 # turn LEFT
    turn1_done = 3
    turn2_done = 4


