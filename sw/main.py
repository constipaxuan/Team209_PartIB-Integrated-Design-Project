#import utime

from machine import Pin, PWM, I2C, ADC
from libs.VL53L0X.VL53L0X import VL53L0X
from time import sleep, sleep_ms, ticks_ms, ticks_diff
#from enum import Enum
from behaviour import Turn_Direction, Turn_State, Mode, Start_States, TNT_states, Delivery_States, Delivery_Rack_States 
from locations import Junctions, Location, Direction, Resistor_Color
from map_state import mapping

# --- CLASSES ---


class Motion:
    follow = 1
    turning = 2

class Motor:
    def __init__(self, dirPin, PWMPin):
        self.mDir = Pin(dirPin, Pin.OUT)  # set motor direction pin
        self.pwm = PWM(Pin(PWMPin))  # set motor pwm pin
        self.pwm.freq(1000)  # set PWM frequency
        self.pwm.duty_u16(0)  # set duty cycle - 0=off
        
    def off(self):
        self.pwm.duty_u16(0)
        
    def Forward(self, speed=100):
        self.mDir.value(0)                     # forward = 0 reverse = 1 motor
        self.pwm.duty_u16(int(65535 * speed / 100))  # speed range 0-100 motor

    def Reverse(self, speed=100):
        self.mDir.value(1)
        self.pwm.duty_u16(int(65535 * speed / 100))



motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 

S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)
laser_distance = 0 #initialize laser distance
button = Pin(14, Pin.IN) # button is a PULL_DOWN so it reads 0 when not pressed and 1 when pressed.
ADC_SOLUTION = 65535  # Pico ADC is 16-bit (0–65535) FOR LEDs
# STOP IMMEDIATELY AFTER RESET
motor_l.Forward(0)
motor_r.Forward(0)

ON = False
prev_button = 0

# --- DICTIONARIES (MUTABLE - DO NOT NEED TO RETURN. HOLDS VALUES ACROSS ITERATIONS) ---
sensors = {
    "S1": 0,
    "S2": 0,
    "SL": 0,
    "SR": 0
}

events = {
    "new_junction": False,
    "new_T": False,
    "on_junction": False,
    "on_T": False,
    "junction_type": Junctions.nil,
    "start_T_shape_count": 0,
    "prev_on_junction" : False,
    "prev_on_T": False
}

robot = {
    "motion": Motion.follow,
    "start_state" : Start_States.start,
    "turn_state": Turn_State.start,
    "turn_dir": Turn_Direction.nil,
    "turn_complete": False,
    "direction": Direction.acw,
    "location": Location.start,
    "mode": Mode.start,
    "timed_turn_started": False,
    "timed_turn_start": 0,
    "target_rack_idx": 0,
    "tnt_state": TNT_states.nil
}

delivery = {
    "delivery_state": Delivery_States.pickup,
    "rack_state": Delivery_Rack_States.load_detected,
    "ready_for_unloading": False,
    "resistor_color": Resistor_Color.none,
    "drop_off_bay": 0,
    "bay_latch": False,
    "unloading_state": False,
    "main_spine_detected": False,
    "turn_phase": 0,
    "target_rack": Location.rack_purple_L,
    "deliv_start_time": 0,
    "R_detected": False,
    "search_slot_counter": 0,
    "slot_status": [0,0,0,0,0,0],
    "rack_switching_bcount" : 0
}

memory = {
    "prev_on_junction" : False,
    "rack_branches_OL" : 0,
    "rack_branches_PL" : 0,
    "rack_branches_OH" : 0,
    "rack_branches_PH" : 0,
    "elevator_low_branches" : 0,
    "elevator_high_branches" : 0,
}


counting = True


# LED wiring
B_led = 19 # pin 19
G_led = 18 # pin 18
R_led = 17 # pin 17
Y_led = 16 # pin 16
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
sensor = ADC(28) #FOR LEDs

#centering code
def line_follow_step(S1, S2, base, corr):

  if (S1 == 1 and S2 == 0): # corrects left veer
    motor_r.Forward(speed = corr) # speed ranges from 0 to 100 as defined
    motor_l.Forward(speed = base)
  elif (S1 == 0 and S2 == 1): #corrects right veer
    motor_l.Forward(speed = corr)
    motor_r.Forward(speed = base)
  else: #centered 
    motor_r.Forward(speed = base)
    motor_l.Forward(speed = base)

def detect_junction_type(SL, SR):
    if (SL == 1 and SR == 0): 
        return Junctions.L
    elif (SL == 0 and SR == 1):
        return Junctions.R
    elif (SL == 1 and SR == 1):
        return Junctions.RL
    return Junctions.nil
   
#This one need to test, its going backwards so idk if the the logic will be reversed.
def back_line_follow_step(S1, S2):
  base = 80
  corr = 20
  
  if (S1 == 0 and S2 == 1): # corrects left veer
    motor_r.Reverse(speed = corr) # speed ranges from 0 to 100 as defined
    motor_l.Reverse(speed = base)
  elif (S1 == 1 and S2 == 0): #corrects right veer
    motor_l.Reverse(speed = corr)
    motor_r.Reverse(speed = base)
  else: #centered 
    motor_r.Reverse(speed = base)
    motor_l.Reverse(speed = base)


def detect_junction_type(SL, SR):
    if (SL == 1 and SR == 0): 
        return Junctions.L
    elif (SL == 0 and SR == 1):
        return Junctions.R
    elif (SL == 1 and SR == 1):
        return Junctions.RL
    return Junctions.nil



# returns True when turn complete, False otherwise. Call in discrete time steps while in turning mode.
# change speed of wheel to match position of ideal pivot (lies on 45 degree line from the corner)
# Prevents original line from being misidentified as the new line by forcing bot to lose the first line before finding the new one.
def turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r):
    if turn_state == Turn_State.start:
        if (S1 == 0 and S2 == 0): # Lost the original line
            turn_state = Turn_State.line_lost

    
    elif turn_state == Turn_State.line_lost:
        if (S1 == 1 and S2 == 1): # Found the new line. 
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            return Turn_State.done, True
        
    if turn_dir == Turn_Direction.left:
        motor_l.Forward(speed = 60)
        motor_r.Forward(speed = 20)

    elif turn_dir == Turn_Direction.right:
        motor_l.Forward(speed = 20)
        motor_r.Forward(speed = 60)
    
    return turn_state, False
    

#turn_state, turn_complete = turn_v4(turn_dir, S1, S2)

turn_complete = False
#first_done = False -- local variables no need to define
#second_done = False
turn_phase = 0 # 0 = first 90, 1 = second 90 for 180 turn
def turn_180(turn_dir, S1, S2, turn_state, turn_phase, motor_l, motor_r):
    if turn_phase == 0:
        turn_state, first_done = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
        if first_done: 
            turn_state = Turn_State.start
            turn_phase = 1

    elif turn_phase == 1:
        turn_state, second_done = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
        if second_done:
            turn_phase = 0
            turn_state = Turn_State.start
            return turn_state, True, turn_phase

    return turn_state, False, turn_phase



def update_start_T_count(start_T_shape_count, new_T):
    #global start_T_shape_count, counting
    if new_T:
        start_T_shape_count += 1
    #print(f"T shapes passed: {start_T_shape_count}")
    return start_T_shape_count


# OK THAT STUFF WORKS NOW

# Call this in discrete time steps while mode = Mode.start
def get_out_of_box(sensors, events, robot, delivery):
    # --- Main Mission Loop ---

    # To prevent double counting: Only can update count while NOT in turning mode.
    if robot["start_state"] == Start_States.start or robot["start_state"] == Start_States.turn1_done:
        events["start_T_shape_count"] = update_start_T_count(events["start_T_shape_count"], events["new_T"])

    if robot["start_state"] == Start_States.start:   
    # State 1: Drive out of the box, drive straight
    #if start_T_shape_count < 2:
        if events["start_T_shape_count"] == 2:
            if sensors["SL"] == 0 and sensors["SR"] == 0: # Move forward until the SL and SR lose the white line. 
                Blue.value(1)
                robot["start_state"] = Start_States.turn1
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["turn_state"] = Turn_State.start
                robot["turn_complete"] = False

        else:
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    # State 2: Hit second T shape, turn clockwise
    elif robot["start_state"] == Start_States.turn1:

        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if  robot["turn_complete"]:
            robot["start_state"] = Start_States.turn1_done
            #print("turn 1 done")
    
    elif robot["start_state"] == Start_States.turn1_done:
        if events["start_T_shape_count"] == 3:
            robot["start_state"] = Start_States.turn2
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            Blue.value(1)

        else:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    elif robot["start_state"] == Start_States.turn2:
        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if robot["turn_complete"]:
            #print("turn 2 COMPLETED")
            robot["start_state"] = Start_States.turn2_done
            delivery["target_rack"] = Location.rack_purple_L
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
            
    
    elif robot["start_state"] == Start_States.turn2_done:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        robot["mode"] = Mode.search_init
        robot["location"] = Location.rack_purple_L
        #print("turn 2 done")

''' upper right refers to the one above purple rack, 
    upper left is above orange rack, 
    unloading is the one turning into unloading bay and 
    back_to_start is the turn back into starting box. 

'''
class Test_Corners:
    upper_right = 1
    upper_left = 2
    unloading = 3
    back_to_start = 4

# test_corner is the next corner to be turned.
test_corner = Test_Corners.upper_right
OB_counter = 0
last_press = 0


# defines turning sequence in line following test 5 Mar.
def test_main_loop(robot, events, test_corner, OB_counter):
    if test_corner == Test_Corners.upper_right:
        if events["new_T"]:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            Red.value(1)
    if test_corner == Test_Corners.upper_left:
        if events["new_junction"]:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            Green.value(1)
    if test_corner == Test_Corners.unloading:
        if OB_counter == 6:
            robot["tnt_state"] = TNT_states.TNT
            print("TNT")
            robot["turn_dir"] = Turn_Direction.left
            OB_counter = 0
            Yellow.value(1)
        else:
            if events["new_T"]:
                OB_counter = 0
            elif events["new_junction"]:
                OB_counter += 1
            robot["tnt_state"] = TNT_states.nil
    if test_corner == Test_Corners.back_to_start:
        if events["new_junction"]:
            robot["tnt_state"] = TNT_states.TNT
            robot["turn_dir"] = Turn_Direction.right
    
    return test_corner, OB_counter


corners = [
    Test_Corners.upper_right,
    Test_Corners.upper_left,
    Test_Corners.unloading,
    Test_Corners.back_to_start
]

corner_idx = 0

#This is the code for initializing laser, need to run everytime we want to use the laser on the right (for lower orange upper purple)
def init_laser_R():
    # config I2C Bus
    i2c_bus = I2C(id=1, sda=Pin(10), scl=Pin(11)) # I2C1 on GP10 & GP11
    # print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
        
    # Setup vl53l0 object
    global vl53l0
    vl53l0 = VL53L0X(i2c_bus)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

#This is the code for initializing laser on the left (for lower purple upper orange)
def init_laser_L():
    # config I2C Bus
    i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
    # print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
        
    # Setup vl53l0 object
    global vl53l0
    vl53l0 = VL53L0X(i2c_bus)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)


#Code for reading distance from laser. detect functons call this.
def rec_dist_laser():
    # Start device
    vl53l0.start()
    # Read one sample
    laser_distance = vl53l0.read()
    # Stop device
    vl53l0.stop()
    return laser_distance


#Code for detecting whether there is a resistor or not for each slot
def R_detect(events, laser_distance, delivery, robot):
#QN: after I detect a resistor, how do I connect the turning function after this? Turning left or right to collect a resistor depends on the rack
    # ONLY act if this is a BRAND NEW junction detection (Does the new junction work here?)
    if events["on_junction"] == True and not events["on_T"] and events["new_junction"] == True:
        # decide which distance sensor to use based on direction of travel
        # 1. Safety check: stop the counter if we run out of slots (All slots have been cleared for a particular rack)
        if delivery["search_slot_counter"] >= 6: # 6 slots
            robot["target_rack_idx"] += 1
            delivery["search_slot_counter"] = 0
            delivery["slot_status"] = [0,0,0,0,0,0] #still need to integrate this into wider system so that it also marks the rack as cleared
            return

        else:
            sleep(0.2) #delay to ensure bot is in position before reading laser
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0) #Stop and measure
            # 2. Find laser distance, fire once
            laser_distance = rec_dist_laser()
             
            # 3. Update the CURRENT slot
            if laser_distance < 100: 
                delivery["R_detected"] = True
                delivery["delivery_state"] = Delivery_States.pickup
                delivery["ready_for_unloading"] = False
                delivery["rack_state"] = Delivery_Rack_States.load_detected
                delivery["search_slot_counter"] += 1
            else:
                delivery["slot_status"][delivery["search_slot_counter"]] = 1
                delivery["search_slot_counter"] += 1
                #mark the slot as cleared
            return laser_distance


# FUNCTION FOR OPENING AND CLOSING THE 3 WIRE CLAW SERVO
#initialize the servo with 3 wires
servo = PWM(Pin(15))
servo.freq(50) # Standard 50Hz frequency

def claw(angle):
    # Map 0-270 degrees to 500-2500 microseconds
    # Pico PWM duty is 0-65535. 
    # 50Hz period is 20ms. 500us = 2.5% duty. 2500us = 12.5% duty.
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)



# FUNCTION FOR TURNING THE PLATFORM THAT HOLDS THE CLAW, 4 wire servo
# Initialize the servo with 4 wires
servo = PWM(Pin(15)) #QN: is this pin correct? It shares the same pin as the 3 wire servo
servo.freq(50)
feedback = ADC(Pin(26)) #this is where the white wire goes

def turn_claw(angle):
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)

#FUNCTION FOR MEASURING THE RESISTANCE ONCE GRABBED AND LIGHTS APPROPRITE LED UP
def R_measure():
    #pass current through and measure voltage V&I
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION 
    #this is the final voltage reading

    if voltage > 3:
        Blue.value(1) #turns LED on to blue
        resistor_color = Resistor_Color.blue # Blue
    elif 2.5 < voltage <= 3:
        Green.value(1)
        resistor_color = Resistor_Color.green # Green
    elif 1 < voltage <= 2.5:
        Red.value(1)
        resistor_color = Resistor_Color.red # Red
    elif 0.2 < voltage <= 1:
        Yellow.value(1)
        resistor_color = Resistor_Color.yellow # Yellow
    return resistor_color

# ---   get out of rack branch test - ends when we turn into green unloading bay. stop at RL. ---
""" prev_on_junction = False
prev_on_T = False
turn_state = Turn_State.start
turn_dir = Turn_Direction.right # assuming starting in orange L
turn_complete = False
turn_phase = 0
motion = Motion.follow

S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6)  

timed_turn_started = False
timed_turn_start = 0
timed_rev_start = 0
timed_rev_started = False
GO_test_bcount = 0
last_branch_time = 0

class Test_GetOut:
    Rev_Branch = 0
    Exiting_Branch = 1
    RackZone = 2
    AwaitingTurn = 3
    Unloading = 4
    UB = 5

getout_state = Test_GetOut.Rev_Branch

def timed_turn_step(timed_turn_started, timed_turn_start, turn_dir, motion):
    if not timed_turn_started:
        timed_turn_started = True
        timed_turn_start = ticks_ms()

    if turn_dir == Turn_Direction.left:
        motor_l.Forward(speed=80)
        motor_r.Reverse(speed=30)
    elif turn_dir == Turn_Direction.right:
        motor_l.Reverse(speed=30)
        motor_r.Forward(speed=80)

    if ticks_diff(ticks_ms(), timed_turn_start) > 1100:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        motion = Motion.follow
        timed_turn_started = False
        return True, timed_turn_started, timed_turn_start, turn_dir, motion

    return False, timed_turn_started, timed_turn_start, turn_dir, motion

while True:
    S1 = S1_sensor.value()
    S2 = S2_sensor.value()
    SL = SL_sensor.value()
    SR = SR_sensor.value()

    button_now = button.value()

    on_junction = (SL == 1 or SR == 1)
    new_junction = (not prev_on_junction) and on_junction
    on_T = (SL  == 1 and SR == 1)
    new_T = (not prev_on_T) and on_T

    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()
    
    prev_button = button_now 

    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]
        continue

    elif ON:
        
        if getout_state == Test_GetOut.Rev_Branch:
            if not timed_rev_started:
                timed_rev_started = True
                timed_rev_start = ticks_ms()

            else:
                motor_l.Reverse(speed=80)
                motor_r.Reverse(speed=80)

            if ticks_diff(ticks_ms(), timed_rev_start) > 1000:   # modify according to needs.
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                motion = Motion.follow
                timed_rev_started = False
                getout_state = Test_GetOut.Exiting_Branch

        elif getout_state == Test_GetOut.Exiting_Branch:

            if motion != Motion.turning:
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)
                motion = Motion.turning
                Blue.value(1)
                print("start timed turn!")
            
            if motion == Motion.turning:
                turn_complete, timed_turn_started, timed_turn_start, turn_dir, motion = timed_turn_step(timed_turn_started, timed_turn_start, turn_dir, motion)
                if turn_complete:
                    turn_complete = False
                    turn_state = Turn_State.start
                    Blue.value(0)
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    getout_state = Test_GetOut.RackZone
                    print("timed turn finished")
                    last_branch_time = ticks_ms()

        elif getout_state == Test_GetOut.RackZone:
            if new_junction:
                last_branch_time = ticks_ms()

            if ticks_diff(ticks_ms(), last_branch_time) > 2500:
                print("out of rack zone")
                getout_state = Test_GetOut.AwaitingTurn
            
            line_follow_step(S1, S2, 80, 20)
                    

        elif getout_state == Test_GetOut.AwaitingTurn:
            
            if motion == Motion.turning:
                turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
                    getout_state = Test_GetOut.Unloading
                    print("in unloading now")

            if motion == Motion.follow:
                line_follow_step(S1, S2, 80, 20)
                if new_junction:
                    turn_dir = Turn_Direction.left
                    turn_complete = False
                    turn_state = Turn_State.start
                    motion = Motion.turning
                    
        
        elif getout_state == Test_GetOut.Unloading:
            
            if motion == Motion.turning:
                turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)
                if turn_complete:
                    motion = Motion.follow
                    turn_complete = False
                    turn_state = Turn_State.start
                    getout_state = Test_GetOut.UB
            
            if motion == Motion.follow:
                line_follow_step(S1, S2, 80, 20)
                if new_junction and motion != Motion.turning:
                    motion = Motion.turning 
                    turn_dir = Turn_Direction.right
                    turn_complete = False
                    turn_state = Turn_State.start
            
        elif getout_state == Test_GetOut.UB:
            if motion == Motion.follow:
                if on_T:
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    print("reached green bay")
                else:
                    line_follow_step(S1, S2, 80, 20)

        prev_on_junction = on_junction   
        prev_on_T = on_T """

# -- LOOP + MAPPING TEST ---
""" while True:
    sensors["S1"] = S1_sensor.value()
    sensors["S2"] = S2_sensor.value()
    sensors["SL"] = SL_sensor.value()
    sensors["SR"] = SR_sensor.value()

    
    button_now = button.value()

    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)            # specifically T-shape / both side sensors active
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]

    #if events["new_junction"]:
    #    events["junction_type"] = detect_junction_type(sensors["SL"], sensors["SR"])
    #else:
    #    events["junction_type"] = Junctions.nil
    #
    #robot["location"] = mapping(robot["location"], robot["mode"], robot["direction"], events["junction_type"])


    # non blocking debouncing. this allows sensors to still be read while button is being debounced, preventing missed junctions.
    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()
    
    prev_button = button_now 
    
    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]
        continue
        
    elif ON:

        if robot["mode"] == Mode.start:
            get_out_of_box(sensors, events, robot, delivery)

        elif robot["mode"] == Mode.search_init:
            # keep following until fully clear of any startup junction/T
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            if not events["on_junction"] and not events["on_T"]:
                robot["motion"] = Motion.follow
                robot["tnt_state"] = TNT_states.nil
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                events["prev_on_junction"] = False
                events["prev_on_T"] = False
                robot["mode"] = Mode.search

        
        else:
            if robot["tnt_state"] == TNT_states.nil:
                test_corner, OB_counter = test_main_loop(robot, events, test_corner, OB_counter)

            if robot["motion"] == Motion.follow:
                if robot["tnt_state"] == TNT_states.TNT:
                    if not events["on_junction"]:
                        robot["tnt_state"] = TNT_states.waiting
                        print("waiting")
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)


                elif robot["tnt_state"] == TNT_states.waiting:
                    if events["new_junction"]:
                        robot["tnt_state"] = TNT_states.NT_is_here
                        print("NT")
                        Red.value(0)
                        Green.value(0)
                        Yellow.value(0)
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

                
                elif robot["tnt_state"] == TNT_states.NT_is_here:
                    sensors["SL"] = SL_sensor.value()
                    sensors["SR"] = SR_sensor.value()
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    robot["motion"] = Motion.turning
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
                    Red.value(1)

                else:
                    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            elif robot["motion"] == Motion.turning:
                if not robot["turn_complete"]:
                    robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)

                else:
                    robot["motion"] = Motion.follow
                    robot["turn_complete"] = False
                    robot["tnt_state"] = TNT_states.nil
                    print(f"location:", robot["location"])
                    Red.value(0)
                    Green.value(0)
                    Yellow.value(0)
                    if corner_idx < len(corners) - 1:
                        corner_idx += 1
                    else:
                        corner_idx = 0
                        if events["on_T"]:
                            motor_l.Forward(speed = 0)
                            motor_r.Forward(speed = 0)
                        else:
                            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
                    
                    test_corner = corners[corner_idx]
                    
    
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"] """

#Resistor detection TEST (Now with line following)

init_laser_R()

while True:
    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)            # specifically T-shape / both side sensors active
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]
    line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
    # pretend we just crossed a junction (update events before calling)
    # call detector using globals; pass previous laser_distance or None
    laser_distance = R_detect(events, laser_distance, delivery, robot)

    # print distance sample and state for debugging
    print(f"Distance reading: {laser_distance}mm")
    print(f"Counter: {delivery['search_slot_counter']}")
    print(f"Slot status: {delivery['slot_status']}")


    # loop continues indefinitely; break manually when done 








