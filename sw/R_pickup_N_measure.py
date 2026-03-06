from map_state import * 
from behaviour import *
from locations import Location
from test_3wireservo import set_angle
from test_4wireservo import set_angle_4wire
from lowerpurple_upper_orange_R_detect import R_detected
from upperpurple_lowerorange_R_detect import R_detected
#use the 3 wire servo for the parallelogram because it has no feedback and the parallelogram has no mechanical resistance anyways

def Pgram_tilt(mode, location): #tilting of parallelogram
    if mode == Mode.delivery:
        # tilt down here
        set_angle(0)
        
    elif mode == Mode.search:
        if location in [Location.rack_orange_L, Location.rack_purple_L]:
            # tilt down here
            set_angle(0)
        elif location in [Location.rack_orange_U, Location.rack_purple_U]:
            # tilt a bit higher to reach the resistors
            set_angle(45)

def claw(R_detected):
    if R_detected == True:
        # close claw to pick up resistor
        set_angle_4wire(0) # might need to adjust angle depending on how the servo is mounted and how the claw is designed
    else:
        # open claw
        set_angle_4wire(90) # might need to adjust angle depending on how the servo is mounted and how the claw is designed

def R_measure_N_LED(R):
    #pass current through and measure voltage V&I
    R = V / I
    if R < 100:
        resistor_color = 0 # Red
        #LED light up red (ADD CODE)
    elif R < 220:
        resistor_color = 1 # Yellow
        #LED light up yellow (ADD CODE)
    elif R < 470:
        resistor_color = 3 # Green
        #LED light up green (ADD CODE)
    else:
        resistor_color = 4 # Blue
        #LED light up blue (ADD CODE)
    return resistor_color



