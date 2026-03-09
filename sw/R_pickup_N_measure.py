from map_state import * 
from behaviour import *
from locations import Location
from test_3wireservo import set_angle
from test_4wireservo import set_angle_4wire
from locations import Resistor_Color
#use the 3 wire servo for the parallelogram because it has no feedback and the parallelogram has no mechanical resistance anyways
from time import sleep
from machine import ADC, Pin
import time
#Rdetected is already a global variable
# Constants (same logic as Arduino code)
ADC_SOLUTION = 65535  # Pico ADC is 16-bit (0–65535)

# LED wiring
B_led = 21 # pin 27
G_led = 20 # pin 26
R_led = 19 # pin 25
Y_led = 18 # pin 24
Blue = Pin(B_led, Pin.OUT)
Green = Pin(G_led, Pin.OUT)
Red = Pin(R_led, Pin.OUT)
Yellow = Pin(Y_led, Pin.OUT)
#Initialize Blue Red Green Yellow color to off
Blue.value(0)
Green.value(0)
Red.value(0)
Yellow.value(0)
# Sensor connected to ADC0 (GP26)
sensor = ADC(26)


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

def grab():
    set_angle_4wire(0) # might need to adjust angle depending on how the servo is mounted and how the claw is designed

def release():
    set_angle_4wire(90) # might need to adjust angle depending on how the servo is mounted and how the claw is designed
def R_measure():
    #pass current through and measure voltage V&I
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION 
    #this is the final voltage reading

    # Turn on correct led
    if voltage > 3:
        Blue.value(1) #turns LED on to blue
        resistor_color = Resistor_Color.blue # Blue
    elif 3 > voltage > 2.5:
        Green.value(1)
        resistor_color = Resistor_Color.green # Green
    elif 2.5 > voltage > 1:
        Red.value(1)
        resistor_color = Resistor_Color.red # Red
    elif 1 > voltage > 0.2:
        Yellow.value(1)
        resistor_color = Resistor_Color.yellow # Yellow
    return resistor_color





