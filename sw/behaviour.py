#from enum import Enum

class Mode():
    start = 0
    search = 1
    delivery = 2

# fill out with servo code
def rotation_tracker():
    pass

#count junctions upon state transition to avoid double counting. Need debouncing as well.
def edge_triggering(junction):
