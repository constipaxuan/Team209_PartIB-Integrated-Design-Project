#import utime

from machine import Pin, PWM, I2C, ADC
from libs.VL53L0X.VL53L0X import VL53L0X
from time import sleep, sleep_ms, ticks_ms, ticks_diff
#from enum import Enum
from behaviour import Turn_Direction, Turn_State, Mode, Start_States, TNT_states, Delivery_States, Delivery_Rack_States, Unloading_States
from locations import Junctions, Location, Direction, Resistor_Color
from decision import handler_blue_bay, handler_green_bay, handler_red_bay, handler_yellow_bay

# --- CLASSES ---
class Get_Out_of_branch:
    Rev_Branch = 0
    Exiting_Branch = 1
    RackZone = 2
    AwaitingTurn = 3

class Motion:
    follow = 1
    turning = 2
    stopped_for_scan = 3

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

class Node:
    Starting_node = 0
    Yellow_bay = 1
    Red_bay = 2
    PL1 = 3
    PL2 = 4
    PL3 = 5
    PL4 = 6
    PL5 = 7
    PL6 = 8
    Purple_T = 9
    Elev_low_P = 10
    Elev_junc = 11
    Elev_low_O = 12
    Orange_T = 13
    OL1 = 14
    OL2 = 15
    OL3 = 16
    OL4 = 17
    OL5 = 18
    OL6 = 19
    Blue_bay = 20
    Green_bay = 21

class Racks:
    rack_orange_L = 0
    rack_purple_L = 1
    rack_orange_U = 2
    rack_purple_U = 3

lower_loop = [Node.Starting_node, Node.Yellow_bay, Node.Red_bay, 
         Node.PL1, Node.PL2, Node.PL3, Node.PL4, Node.PL5, Node.PL6, Node.Purple_T, 
         Node.Elev_low_P, Node.Elev_junc, Node.Elev_low_O,
         Node.Orange_T, Node.OL1, Node.OL2, Node.OL3, Node.OL4, Node.OL5, Node.OL6,
         Node.Blue_bay, Node.Green_bay]

N = len(lower_loop)

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
    "gnd_loc_idx": 0,
    "mode": Mode.start,
    "timed_turn_started": False,
    "timed_turn_start": 0,
    "target_rack_idx": 0,
    "tnt_state": TNT_states.nil,
    "scan_start": 0,
    "just_turned": False
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
    "deliv_start_time": 0,
    "R_detected": False,
    "search_slot_counter": 0,
    "slot_status": [0,0,0,0,0,0],
    "rack_switching_bcount" : 0,
    "rack_cleared" : False,
    "getout_state": Get_Out_of_branch.Rev_Branch,
    "timed_rev_started": False,
    "timed_rev_start": 0,
    "last_branch_time": 0
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

target_racks = [Racks.rack_purple_L, Racks.rack_orange_L, Racks.rack_purple_U, Racks.rack_orange_U]

# --- LED wiring ---
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

# --- TURNING ---
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

# robot["turn_complete"] = timed_turn_step(robot, time_ms)
def timed_turn_step(robot, time_ms):
    if not robot["timed_turn_started"]:
        robot["timed_turn_started"] = True
        robot["timed_turn_start"] = ticks_ms()

    if robot["turn_dir"] == Turn_Direction.left:
        motor_l.Forward(speed=80)
        motor_r.Forward(speed=0)
    elif robot["turn_dir"] == Turn_Direction.right:
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=80)

    if ticks_diff(ticks_ms(), robot["timed_turn_start"]) > time_ms:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        robot["motion"] = Motion.follow
        robot["timed_turn_started"] = False
        return True

    return False

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

    # start_T_shape_count is only used for getting out of box, after that on main loop use gnd_loc_idx.
    if robot["start_state"] == Start_States.start:
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
                robot["gnd_loc_idx"] = 0 # set to 0
                robot["motion"] = Motion.turning

        else:
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    # State 2: Hit second T shape, turn clockwise
    elif robot["start_state"] == Start_States.turn1:

        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if  robot["turn_complete"]:
            robot["start_state"] = Start_States.turn1_done
            robot["motion"] = Motion.follow
            #print("turn 1 done")
    
    elif robot["start_state"] == Start_States.turn1_done:
        if robot["gnd_loc_idx"] == 2: #red bay
            robot["start_state"] = Start_States.turn2
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            robot["motion"] = Motion.turning
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
            robot["motion"] = Motion.follow
            Blue.value(0)
            
            
    
    elif robot["start_state"] == Start_States.turn2_done:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        robot["mode"] = Mode.search_init
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
def test_main_loop(robot, events, test_corner):
    if test_corner == Test_Corners.upper_right:
        if robot["gnd_loc_idx"] == :
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
def rec_dist_laserR():
    # config I2C Bus
    i2c_bus = I2C(id=1, sda=Pin(10), scl=Pin(11), freq=100000) # I2C1 on GP10 & GP11
    # Setup vl53l0 object
    vl53l0_R
    vl53l0_R = VL53L0X(i2c_bus)
    vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[0], 18)
    vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[1], 14)
    laser_distance = vl53l0_R.read()
    return laser_distance

#This is the code for initializing laser on the left (for lower purple upper orange)
def rec_dist_laserL():
    # config I2C Bus
    i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
    # print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
        
    # Setup vl53l0 object
    vl53l0_L
    vl53l0_L = VL53L0X(i2c_bus)
    vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[0], 18)
    vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[1], 14)
    laser_distance = vl53l0_L.read()
    return laser_distance


    
    
# --- RESISTOR DETECTION - Keep as it is---
def rack_search(sensors, events, robot, delivery):
    if robot["motion"] == Motion.follow:
            if robot["gnd_rack_idx"] in [3, 4, 5, 6, 7, 8, 14, 15, 16, 17, 18 ,19]:
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                robot["motion"] = Motion.stopped_for_scan
                robot["scan_start"] = ticks_ms()
            else:
                line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        

    elif robot["motion"] == Motion.stopped_for_scan:
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)

        if ticks_diff(ticks_ms(), robot["scan_start"]) >= 30: # edit
            if target_racks[robot["target_rack_idx"]] == Location.rack_purple_L or target_racks[robot["target_rack_idx"]] == Location.rack_orange_U:
                laser_distance = rec_dist_laserL()
            elif target_racks[robot["target_rack_idx"]] == Location.rack_purple_U or target_racks[robot["target_rack_idx"]] == Location.rack_orange_L:
                laser_distance = rec_dist_laserR()
            print("NEW distance:", laser_distance)
            print("slot counter:", delivery["search_slot_counter"])
            print("slot status:", delivery["slot_status"])

            if laser_distance < 100:
                Red.value(1)
                delivery["R_detected"] = True
                delivery["delivery_state"] = Delivery_States.pickup
                delivery["ready_for_unloading"] = False
                delivery["rack_state"] = Delivery_Rack_States.approaching
                delivery["search_slot_counter"] += 1

                robot["turn_complete"] = False
                robot["timed_turn_started"] = False
                robot["motion"] = Motion.turning

                if robot["direction"] == Direction.cw:
                    robot["turn_dir"] = Turn_Direction.right
                elif robot["direction"] == Direction.acw:
                    robot["turn_dir"] = Turn_Direction.left
                
                return

            else:
                delivery["slot_status"][delivery["search_slot_counter"]] = 1
                robot["motion"] = Motion.follow

                if delivery["search_slot_counter"] < 5: #changed 6 to 5
                    delivery["search_slot_counter"] += 1
                else:
                    delivery["search_slot_counter"] = 0
                    robot["motion"] = Motion.follow
                    delivery["rack_cleared"] = True
                    robot["target_rack_idx"] = (robot["target_rack_idx"] + 1) % 4
                    delivery["slot_status"] = [0,0,0,0,0,0]
                    robot["motion"] = Motion.follow
                    return
    
    elif robot["motion"] == Motion.turning:
        robot["turn_complete"] = timed_turn_step(robot, 1000)
        if robot["turn_complete"] == True:
            robot["mode"] = Mode.delivery
            robot["motion"] = Motion.follow 
            robot["gnd_loc_idx"] = 0 # reinitialising it bc bot is unable to orient itself atp.              
            return

    


# --- Keep as it is ---
def handler_orange_L_delivery(sensors, events, robot, delivery):
    # Step 1: Enter delivery mode when laser has turned into branch. 
        
    if delivery["rack_state"] == Delivery_Rack_States.approaching:
        #print("APPROACHING 2")
        if not delivery["timed_rev_started"]:
                delivery["timed_rev_started"] = True
                delivery["timed_rev_start"] = ticks_ms()

        else:
            #print("FOLLOW")
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            if ticks_diff(ticks_ms(), delivery["timed_rev_start"]) > 700:   # modify according to needs.
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                delivery["timed_rev_started"] = False
                delivery["rack_state"] = Delivery_Rack_States.reached
                Red.value(0)
          
    
    # MODIFIED FOR TESTING
    # Step 3: Grab the load. Adjust timing in R_measure so that the claw can shut before the bot starts reversing. atp IDGAF is this part is blocking.
    elif delivery["rack_state"] == Delivery_Rack_States.reached:
        sleep_ms(400) 
        delivery["resistor_color"] = Resistor_Color.green #measure the resistor color and store it as a variable so that the bot knows which bay to drop it off at
        delivery["rack_state"] = Delivery_Rack_States.reorienting
        robot["motion"] = Motion.turning
        robot["turn_dir"] = Turn_Direction.right # Face the unloading bay.
        robot["timed_turn_started"] = False
    
    # Step 4: Reverse and turn towards unloading.

    elif delivery["rack_state"] == Delivery_Rack_States.reorienting:
        if delivery["getout_state"] == Get_Out_of_branch.Rev_Branch:
            if not delivery["timed_rev_started"]:
                delivery["timed_rev_started"] = True
                delivery["timed_rev_start"] = ticks_ms()

            else:
                motor_l.Reverse(speed=80)
                motor_r.Reverse(speed=80)

            if ticks_diff(ticks_ms(), delivery["timed_rev_start"]) > 1200:   # modify according to needs.
                motor_l.Forward(speed=0)
                motor_r.Forward(speed=0)
                robot["motion"] = Motion.follow
                delivery["timed_rev_started"] = False
                delivery["getout_state"] = Get_Out_of_branch.Exiting_Branch

        elif delivery["getout_state"] == Get_Out_of_branch.Exiting_Branch:
            if robot["motion"] != Motion.turning:
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)
                robot["motion"] = Motion.turning
                Blue.value(1)
                print("start timed turn!")
            
            if robot["motion"] == Motion.turning:
                robot["turn_complete"] = timed_turn_step(robot, 1200)
                if robot["turn_complete"]:
                    robot["turn_complete"] = False
                    robot["turn_state"] = Turn_State.start
                    Blue.value(0)
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                    delivery["getout_state"] = Get_Out_of_branch.RackZone
                    print("timed turn finished")
                    delivery["last_branch_time"] = ticks_ms()

        # On the straight, need to get out of rack zone.
        elif delivery["getout_state"] == Get_Out_of_branch.RackZone:
            if events["new_junction"]:
                delivery["last_branch_time"] = ticks_ms()

            if ticks_diff(ticks_ms(), delivery["last_branch_time"]) > 2500:
                print("out of rack zone")
                delivery["getout_state"] = Get_Out_of_branch.Rev_Branch #reset
                delivery["rack_state"] = Delivery_Rack_States.load_detected #reset to search for next load after passing each branch, since each bay has 6 branches.
                delivery["ready_for_unloading"] = True
                robot["gnd_loc_idx"] = 19 #OL6
            
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)



def LHS_dropoff(sensors, events, robot, delivery):
    # ASSIGNING TARGET BAY
    if delivery["resistor_color"] == Resistor_Color.red: 
        delivery["target_bay"] = 2 # Red, which is the rightmost bay
    elif delivery["resistor_color"] == Resistor_Color.yellow: 
        delivery["target_bay"] = 1 # Yellow
    elif delivery["resistor_color"] == Resistor_Color.green: 
        delivery["target_bay"] = 21 # Green, skip 1 to skip the starting box
    elif delivery["resistor_color"] == Resistor_Color.blue: 
        delivery["target_bay"] = 20 # Blue 


    # State machine 
    if delivery["unloading_state"] == Unloading_States.finding_bay:
            
        # TARGET DETECTION  
        # case when the target bay is blue, no need to turn -- blue bay is literally straight ahead. 
        if delivery["resistor_color"] == Resistor_Color.blue:
            if robot["gnd_loc_idx"] == 20: # blue bay node.
                delivery["unloading_state"] = Unloading_States.found_bay
                
        else:
        # Turning into unloading corridoor if target bay is not blue. Motion = turning when correct bay is found. Handled in decision loop.
            if robot["gnd_loc_idx"] == 20 and robot["motion"] != Motion.turning:
                robot["motion"] = Motion.turning
                robot["turn_state"] = Turn_State.start
                robot["turn_dir"] = Turn_Direction.left
                    
    elif delivery["resistor_color"] != Resistor_Color.blue and delivery["unloading_state"] == Unloading_States.counting_bays:

        if robot["gnd_loc_idx"] == delivery["target_bay"] and robot["motion"] != Motion.turning:
            print("Target reached! Turning into bay")
            robot["motion"] = Motion.turning
            robot["turn_state"] = Turn_State.start
            robot["turn_dir"] = Turn_Direction.right

    # --- MODIFIED FOR TESTING W/O GRABBER ---
    elif delivery["unloading_state"] == Unloading_States.found_bay:
        if events["new_T"]: #arrived at box
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            #release() #release grabber
            delivery["unloading_state"] = Unloading_States.done
    
    # Motion Control: Called exactly ONCE per iteration
    if robot["motion"] == Motion.follow:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
    elif robot["motion"] == Motion.turning:
        robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r) #turn into box
        if robot["turn_complete"]:
            robot["turn_state"] = Turn_State.start #reset turn state for next turn
            robot["turn_complete"] = False
            robot["motion"] = Motion.follow 
            
            if delivery["unloading_state"] == Unloading_States.finding_bay:
                delivery["unloading_state"] = Unloading_States.counting_bays
            elif delivery["unloading_state"] == Unloading_States.counting_bays:
                delivery["unloading_state"] = Unloading_States.found_bay

def delivery_from_orange_L(sensors, events, robot, delivery):
    if delivery["delivery_state"] == Delivery_States.pickup:
        if delivery["ready_for_unloading"] == False:
            handler_orange_L_delivery(sensors, events, robot, delivery)
        elif delivery["ready_for_unloading"] == True:
            delivery["ready_for_unloading"] = False #reset for next load
            delivery["delivery_state"] = Delivery_States.unloading
        
    elif delivery["delivery_state"] == Delivery_States.unloading:
        LHS_dropoff(sensors, events, robot, delivery) 
        if delivery["unloading_state"] == Unloading_States.done:
            delivery["delivery_state"] = Delivery_States.recover
            delivery["unloading_state"] = Unloading_States.finding_bay
    
    elif delivery["delivery_state"] == Delivery_States.recover:
    #enter unloading bay with blue closest
    # LHS dropoff stops when load has been deposited
        if delivery["resistor_color"] == Resistor_Color.red:
            handler_red_bay(sensors, events, robot, delivery)
        elif delivery["resistor_color"] == Resistor_Color.yellow:
            handler_yellow_bay(sensors, events, robot, delivery)
        elif delivery["resistor_color"] == Resistor_Color.green:
            handler_green_bay(sensors, events, robot, delivery)   
        elif delivery["resistor_color"] == Resistor_Color.blue:
            handler_blue_bay(sensors, events, robot, delivery) # becomes mode search after this func ends.

# FUNCTION FOR OPENING AND CLOSING THE 3 WIRE CLAW SERVO
#initialize the servo with 3 wires (Different servos should be different pins)
servo_claw = PWM(Pin(13))
servo_claw.freq(50) # Standard 50Hz frequency

def claw(angle):
    # Map 0-270 degrees to 500-2500 microseconds
    # Pico PWM duty is 0-65535. 
    # 50Hz period is 20ms. 500us = 2.5% duty. 2500us = 12.5% duty.
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_claw.duty_u16(duty)



# FUNCTION FOR TURNING THE PLATFORM THAT HOLDS THE CLAW, 4 wire servo
# Initialize the servo with 4 wires
servo_tilt = PWM(Pin(15)) #QN: is this pin correct? It shares the same pin as the 3 wire servo
servo_tilt.freq(50)
feedback = ADC(Pin(26)) #this is where the white wire goes

def turn_claw(angle):
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_tilt.duty_u16(duty)

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
while True:
    sensors["S1"] = S1_sensor.value()
    sensors["S2"] = S2_sensor.value()
    sensors["SL"] = SL_sensor.value()
    sensors["SR"] = SR_sensor.value()

    
    button_now = button.value()

    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)            # specifically T-shape / both side sensors active
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]

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

        if events["new_junction"] and robot["motion"] == Motion.follow:
            if robot["direction"] == Direction.acw:
                robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] + 1) % N
            if robot["direction"] == Direction.cw:
                robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] - 1) % N

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

            if robot["gnd_loc_idx"] in [10, 12, 20, 0]:
                robot["motion"] = Motion.turning
            
            if robot["motion"] == Motion.follow:
                line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
            elif robot["motion"] == Motion.turning:
                if not robot["turn_complete"]:
                    robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
                    if robot["turn_complete"]:
                        robot["turn_state"] = Turn_State.start
                        robot["turn_complete"] = False
                        robot["motion"] = Motion.follow
                        robot["just_turned"] = True       
    
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]


#Resistor detection TEST (Now with line following)

""" laser_distance = None

sleep_ms(100)
init_laser_R()
sleep_ms(50)
vl53l0.start()

robot["mode"] = Mode.search
robot["direction"] = Direction.cw
# Start device


while True:

    sensors["S1"] = S1_sensor.value()
    sensors["S2"] = S2_sensor.value()
    sensors["SL"] = SL_sensor.value()
    sensors["SR"] = SR_sensor.value()

    button_now = button.value()

    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()
    
    prev_button = button_now 


    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)            # specifically T-shape / both side sensors active
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]

    if events["new_junction"] and robot["motion"] == Motion.follow:
        if robot["direction"] == Direction.acw:
            gnd_loc_idx = (robot["gnd_loc_idx"] + 1) % N
        if robot["direction"] == Direction.cw:
            gnd_loc_idx = (robot["gnd_loc_idx"] - 1) % N


    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]
        #vl53l0.stop()
        continue

    elif ON:
        if robot["mode"] == Mode.search:
            rack_search(sensors, events, robot, delivery)
        elif robot["mode"] == Mode.delivery:
            delivery_from_orange_L(sensors, events, robot, delivery)

        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]

        sleep_ms(10) """

# --- FINAL MODEL ---
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
        if events["new_junction"] and robot["motion"] == Motion.follow:
            if robot["direction"] == Direction.acw:
                robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] + 1) % N
            if robot["direction"] == Direction.cw:
                robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] - 1) % N

        if robot["mode"] == Mode.start:
            get_out_of_box(sensors, events, robot, delivery)

        elif robot["mode"] == Mode.search_init:
            # keep following until fully clear of any startup junction/T
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

            if not events["on_junction"] and not events["on_T"]:
                robot["motion"] = Motion.follow
                #robot["tnt_state"] = TNT_states.nil
                robot["turn_complete"] = False
                robot["turn_state"] = Turn_State.start
                events["prev_on_junction"] = False
                events["prev_on_T"] = False
                robot["mode"] = Mode.search
                delivery["target_rack"] = Racks.rack_purple_L
                robot["direction"] = Direction.acw
        
        elif robot["mode"] == Mode.search:
            # Purple rack will be the first target rack upon RESET. I will fix the bot to approach in acw direction.
            if target_racks[robot["target_rack_idx"]] == Racks.rack_purple_L:
                # if gnd_loc_idx reaches 9 it means that target_rack has changed to orange_lower
                if robot["gnd_loc_idx"] in range(3, 9): #between PL1 and purple T
                    rack_search(sensors, events, robot, delivery)

            if target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L:
                if robot["gnd_loc_idx"] in range(14, 20): #between OL1 and blue bay
                    rack_search(sensors, events, robot, delivery)
                
        # I assume that while transiting from one state to another the bot will not somehow end up in an illogical position.
            if robot["gnd_loc_idx"] in [2, 10, 12, 20]: # these are corners where you HAVE to turn at or you will CRASH
                if robot["direction"] == Direction.acw:
                    if robot["motion"] != Motion.turning and robot["just_turned"] == False:
                        robot["motion"] = Motion.turning
                        robot["turn_dir"] = Turn_Direction.left

                if robot["direction"] == Direction.cw:
                    if robot["motion"] != Motion.turning and robot["just_turned"] == False:
                        robot["motion"] = Motion.turning
                        robot["turn_dir"] = Turn_Direction.right
            
            if robot["motion"] == Motion.follow:
                line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
            elif robot["motion"] == Motion.turning:
                if not robot["turn_complete"]:
                    robot["turn_state"], robot["turn_complete"] = turn_v4(robot["turn_dir"], sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
                    if robot["turn_complete"]:
                        robot["turn_state"] = Turn_State.start
                        robot["turn_complete"] = False
                        robot["motion"] = Motion.follow
                        robot["just_turned"] = True
        
            if robot["just_turned"] == True and events["new_junction"]:
                robot["just_turned"] = False

        elif robot["mode"] == Mode.delivery:
            if target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L:
                delivery_from_orange_L(sensors, events, robot, delivery)
        
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"] """




""" # pretend we just crossed a junction (update events before calling)
        # call detector using globals; pass previous laser_distance or None
        new_distance = R_detect(events, laser_distance, delivery, robot)

        if new_distance is not None:
            laser_distance = new_distance
            # print distance sample and state for debugging
            print(f"Distance reading: {laser_distance}mm")
            print(f"Counter: {delivery['search_slot_counter']}")
            print(f"Slot status: {delivery['slot_status']}") """
