#import utime

from machine import Pin, PWM, I2C, ADC
from libs.VL53L0X.VL53L0X import VL53L0X
from time import sleep, sleep_ms, ticks_ms, ticks_diff
#from enum import Enum
from behaviour import Turn_Direction, Turn_State, Mode, Start_States, TNT_states, Delivery_States, Delivery_Rack_States, Unloading_States
from locations import Junctions, Location, Direction, Resistor_Color
#from decision import handler_blue_bay, handler_green_bay, handler_red_bay, handler_yellow_bay

# --- CLASSES ---
class Get_Out_of_branch:
    # robot states for the process of reversing out of branch in rack zone
    Rev_Branch = 0
    Exiting_Branch = 1
    RackZone = 2
    AwaitingTurn = 3

class Motion:
    # robot motion states
    follow = 1
    turning = 2
    stopped_for_scan = 3
    reversing = 4

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
    # nodes present in the lower floor
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
    rack_purple_L = 0
    rack_orange_L = 1
    rack_purple_U = 2
    rack_orange_U = 3

class Claw_State:
    idle = 0
    start = 1
    waiting = 2
    done = 3

lower_loop = [Node.Starting_node, Node.Yellow_bay, Node.Red_bay, 
         Node.PL1, Node.PL2, Node.PL3, Node.PL4, Node.PL5, Node.PL6, Node.Purple_T, 
         Node.Elev_low_P, Node.Elev_junc, Node.Elev_low_O,
         Node.Orange_T, Node.OL1, Node.OL2, Node.OL3, Node.OL4, Node.OL5, Node.OL6,
         Node.Blue_bay, Node.Green_bay]

N = len(lower_loop)

TURN_NODES = {2, 10, 12, 20} # Corner nodes where turning must occur to prevent colliding with wall
PURPLE_ZONE_NODES = set(range(3, 9)) 
ORANGE_ZONE_NODES = set(range(14, 20))

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
CLAW_OPERATION_DURATION = 5500
# STOP IMMEDIATELY AFTER RESET
motor_l.Forward(0)
motor_r.Forward(0)

ON = False
prev_button = 0

# Initialise lasers ONCE

i2c_bus = I2C(id=1, sda=Pin(10), scl=Pin(11), freq=100000) # I2C1 on GP10 & GP11
vl53l0_R = VL53L0X(i2c_bus)
vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[0], 18)
vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[1], 14)

i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
vl53l0_L = VL53L0X(i2c_bus)
vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[0], 18)
vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[1], 14)

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
    "direction": Direction.cw,
    "location": Location.start,
    "gnd_loc_idx": 0,
    "mode": Mode.start,
    "timed_turn_started": False,
    "timed_turn_start": 0,
    "timed_move_started": False,
    "timed_move_start": 0,
    "timed_rev_started": False,
    "timed_rev_start": 0,
    "move_complete": False,
    "target_rack_idx": 0,
    "scan_start": 0,
    "just_turned": False,
    "junction_lock": False,
    "claw_state": Claw_State.idle,
    "claw_started": False,
    "claw_start": 0,
    "pending_resync": False,
    "pending_resync_node": 0
}

delivery = {
    "delivery_state": Delivery_States.pickup,
    "rack_state": Delivery_Rack_States.approaching,
    "resistor_color": Resistor_Color.none,
    "unloading_state": False,
    "main_spine_detected": False,
    "search_slot_counter": 0,
    "slot_status": [0,0,0,0,0,0],
    "getout_state": Get_Out_of_branch.Rev_Branch,
    "last_branch_time": 0,
}

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
laser_distance = None
last_press = 0
current_claw_angle = 135
servo_claw = PWM(Pin(13))
servo_claw.freq(50)
def set_angle_slow(current_angle, target_angle, speed_delay):
    # Efficiency check: If we are already there, don't do anything
    if current_angle == target_angle:
        return target_angle

    step = 1 if target_angle > current_angle else -1
    
    for angle in range(current_angle, target_angle + step, step):
        pulse_width = 500 + (angle / 270) * 2000
        duty = int((pulse_width / 20000) * 65535)
        
        servo_claw.duty_u16(duty)
        sleep(speed_delay)
    return target_angle 

#Grabbing & Initialize functions
def grab():
    start_time = ticks_ms()
    print("grab called")
    while ticks_diff(ticks_ms(), start_time) < CLAW_OPERATION_DURATION:
            #Moves the claw from its current position to 90 degrees.
            global current_claw_angle
            current_claw_angle = set_angle_slow(current_claw_angle, 100, 0.01)

def release():
    start_time = ticks_ms()
    print("release called")
    while ticks_diff(ticks_ms(), start_time) < CLAW_OPERATION_DURATION:
            #Moves the claw from its current position to 160 degrees.
            global current_claw_angle
            current_claw_angle = set_angle_slow(current_claw_angle, 180, 0.01)

release() #idle position of claw opening

# --- BUTTON ---
def handle_button(button_now, prev_button, last_press, ON):
    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()

    prev_button = button_now
    return ON, prev_button, last_press

# --- LINE FOLLOWING ---
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
def timed_turn_step(robot, time_ms):
    if not robot["timed_turn_started"]:
        robot["timed_turn_started"] = True
        robot["timed_turn_start"] = ticks_ms()

    if robot["turn_dir"] == Turn_Direction.left:
        motor_l.Forward(speed=82)
        motor_r.Forward(speed=0)
    elif robot["turn_dir"] == Turn_Direction.right:
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=82)

    if ticks_diff(ticks_ms(), robot["timed_turn_start"]) > time_ms:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        robot["motion"] = Motion.follow
        robot["timed_turn_started"] = False
        return True

    return False

# reset robot states to prevent stale states before starting a turn
def start_turn(robot, turn_dir):
    robot["motion"] = Motion.turning
    robot["turn_dir"] = turn_dir
    robot["turn_state"] = Turn_State.start
    robot["timed_turn_started"] = False
    robot["turn_complete"] = False
    #print(f"START TURN: {turn_dir} at node {robot['gnd_loc_idx']} | motion={robot['motion']}")

# reset robot states accordingly when a turn finishes to allow for line following to resume and to mark the completion of a turn
def finish_turn(robot):
    robot["motion"] = Motion.follow
    robot["turn_state"] = Turn_State.start
    robot["turn_complete"] = False
    robot["timed_turn_started"] = False
    robot["just_turned"] = True
    motor_l.Forward(speed = 0)
    motor_r.Forward(speed = 0)
    #print(f"TURN COMPLETE: now following, node={robot['gnd_loc_idx']}")
    
# --- TIMED FORWARD/BACKWARD MOTION ---
#robot["move_complete"] = timed_forward_step(robot, time_ms)
def timed_forward_step(robot, time_ms):
    if not robot["timed_move_started"]:
        robot["timed_move_started"] = True
        robot["timed_move_start"] = ticks_ms()
    
    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

    if ticks_diff(ticks_ms(), robot["timed_move_start"]) > time_ms:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        robot["timed_move_started"] = False
        return True

    return False

def timed_reverse_step(robot, time_ms):
    if not robot["timed_rev_started"]:
        robot["timed_rev_started"] = True
        robot["timed_rev_start"] = ticks_ms()
    
    motor_l.Reverse(speed = 82)
    motor_r.Reverse(speed = 82)

    if ticks_diff(ticks_ms(), robot["timed_rev_start"]) > time_ms:   # modify according to needs.
        motor_l.Forward(speed=0)
        motor_r.Forward(speed=0)
        robot["timed_rev_started"] = False
        return True

    return False

# --- UPDATED EVERY ITERATION ---
def update_sensors_and_events(sensors, events):
    sensors["S1"] = S1_sensor.value()
    sensors["S2"] = S2_sensor.value()
    sensors["SL"] = SL_sensor.value()
    sensors["SR"] = SR_sensor.value()

    events["on_junction"] = (sensors["SL"] == 1 or sensors["SR"] == 1)
    events["new_junction"] = (not events["prev_on_junction"]) and events["on_junction"]

    events["on_T"] = (sensors["SL"] == 1 and sensors["SR"] == 1)          
    events["new_T"] = (not events["prev_on_T"]) and events["on_T"]

# --- LATCHING --- prevents double counting the same junction. 
def latch_events(events):
    events["prev_on_junction"] = events["on_junction"]
    events["prev_on_T"] = events["on_T"]

# --- LOCATION UPDATING --- location is updated upon meeting a new junction
def update_location(robot, events):
    if robot["motion"] != Motion.follow:
        return

    if robot["junction_lock"]:
        if not events["on_junction"]:
            robot["junction_lock"] = False
        return

    if events["new_junction"]:
        robot["junction_lock"] = True

        if robot["just_turned"]:
            robot["just_turned"] = False

        old = robot["gnd_loc_idx"]

        if robot["direction"] == Direction.acw:
            robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] + 1) % N
        elif robot["direction"] == Direction.cw:
            robot["gnd_loc_idx"] = (robot["gnd_loc_idx"] - 1) % N

        dbg(f"NODE {old} -> {robot['gnd_loc_idx']}")

def target_is_purple_L(robot):
    return target_racks[robot["target_rack_idx"]] == Racks.rack_purple_L

def target_is_orange_L(robot):
    return target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L


def in_purple_L_zone(robot):
    return robot["gnd_loc_idx"] in PURPLE_ZONE_NODES

def in_orange_L_zone(robot):
    return robot["gnd_loc_idx"] in ORANGE_ZONE_NODES

def at_target_rack_zone(robot):
    return (
        (target_is_purple_L(robot) and in_purple_L_zone(robot))
        or
        (target_is_orange_L(robot) and in_orange_L_zone(robot))
    )

# --- TURNING DECISIONS ---
def should_turn_here(robot, events):
    '''
        True when the robot reaches a corner node where turning is necessary to prevent a collision.
    '''
    return events["new_junction"] and robot["gnd_loc_idx"] in TURN_NODES

def get_turn_dir(robot):
    '''
        Accurate for corner nodes on main loop where turning is necessary to prevent collision with wall.
    '''
    if robot["direction"] == Direction.acw:
        return Turn_Direction.left
    elif robot["direction"] == Direction.cw:
        return Turn_Direction.right


# --- RESISTOR SCANNING (SEARCH MODE): ENTER DELIVERY MODE IF LOAD DETECTED ---
#This is the code for initializing laser, need to run everytime we want to use the laser on the right (for lower orange upper purple)
def rec_dist_laserR():
    laser_distance = vl53l0_R.read()
    return laser_distance

#This is the code for initializing laser on the left (for lower purple upper orange)
def rec_dist_laserL():
    laser_distance = vl53l0_L.read()
    return laser_distance


def start_rack_scan(robot, delivery):
    '''
        Stops the robot when it reaches a branch in a rack zone. This marks the start of load scanning.
    '''
    motor_l.Forward(speed=0)
    motor_r.Forward(speed=0)

    robot["motion"] = Motion.stopped_for_scan
    robot["scan_start"] = ticks_ms()

    Yellow.value(1)

def update_rack_scan(robot, delivery):
    '''
        Laser reading only taken after the bot has stopped for 50ms to ensure stable reading. 
        Laser reading is taken and compared with a threshold of 250 to decide whether a load is present.
    '''
    motor_l.Forward(speed=0)
    motor_r.Forward(speed=0)

    if ticks_diff(ticks_ms(), robot["scan_start"]) < 50:
        return

    Yellow.value(0)

    laser_distance = read_rack_laser(robot)

    if laser_distance < 250: 
        handle_rack_load_detected(robot, delivery, laser_distance)
    else:
        handle_rack_empty_slot(robot, delivery, laser_distance)
    
def read_rack_laser(robot):
    '''
        Decides which (right or left -- whichever is facing the rack) ToF reading to take for load detection.
    '''
    target_rack = target_racks[robot["target_rack_idx"]]

    if target_rack in [Racks.rack_purple_L, Racks.rack_orange_U]:
        return rec_dist_laserL()

    if target_rack in [Racks.rack_purple_U, Racks.rack_orange_L]:
        return rec_dist_laserR()

    print("WARNING: unknown target rack in read_rack_laser()")
    return 9999

def handle_rack_load_detected(robot, delivery, laser_distance):
    '''
        If load is detected: Enter delivery mode
    '''
    print(
        f"LOAD_DETECTED | slot={delivery['search_slot_counter']} "
        f"| dist={laser_distance} | node={robot['gnd_loc_idx']} "
        f"| motion_before={robot['motion']}"
    ) 
    Red.value(1)

    delivery["delivery_state"] = Delivery_States.pickup
    delivery["rack_state"] = Delivery_Rack_States.approaching
    robot["motion"] = Motion.reversing

def start_rack_pickup_turn(robot):
    '''
        Resets robot states to prevent stale states, allows robot to turn without issues.
    '''
    start_turn(robot, get_turn_dir(robot))

def handle_rack_empty_slot(robot, delivery, laser_distance):
    '''
        If no load detected: slot is marked '1' in the array delivery["slot_status"] to indicate that it has been cleared.
    '''
    slot = delivery["search_slot_counter"]

    #print(f"EMPTY_SLOT | slot={slot} | dist={laser_distance}")
    Green.value(1)

    delivery["slot_status"][slot] = 1
    robot["motion"] = Motion.follow

    # If every slot has been cleared, rack search for that rack is complete.
    if slot < 5:
        delivery["search_slot_counter"] += 1
        #print(f"ADVANCE_TO_NEXT_SLOT | next_slot={delivery['search_slot_counter']}")
    else:
        finish_rack_search(robot, delivery)

def finish_rack_search(robot, delivery):
    '''
        Called when the rack has been cleared completely and target rack is changed to the next one.
    '''
    #print("RACK_CLEARED")

    delivery["search_slot_counter"] = 0
    delivery["slot_status"] = [0, 0, 0, 0, 0, 0]

    robot["target_rack_idx"] = (robot["target_rack_idx"] + 1) % 4
    robot["motion"] = Motion.follow

    #print(f"NEXT_TARGET_RACK_IDX = {robot['target_rack_idx']}")

def update_rack_search_turn(robot):
    '''
        Handles turning from main loop path INTO the rack branch.
    '''
    robot["turn_complete"] = timed_turn_step(robot, 3000)

    if not robot["turn_complete"]:
        return

    print("RACK_PICKUP_TURN_DONE -> Mode.delivery")
    Red.value(0)
    robot["mode"] = Mode.delivery

    finish_turn(robot)

    # temporary re-sync hack
    robot["gnd_loc_idx"] = 0
    
def rack_search(sensors, events, robot, delivery):
    """
    Local handler for searching along a rack. Called when the bot is in search mode and within the rack area. 
    If a load is detected: Finishes when the robot has finished turning into the branch where a load has been detected.
    """

    #print(
    #    f"RACK_SEARCH_TOP | motion={robot['motion']} "
    #    f"| node={robot['gnd_loc_idx']} "
    #    f"| new_junction={events['new_junction']}"
    #)

    if robot["motion"] == Motion.reversing:
        done = timed_reverse_step(robot, 520)
        if not done:
            return  
        #print("REVERSE DONE | direction =", robot["direction"], "| turn_dir =", get_turn_dir(robot))
        start_turn(robot, get_turn_dir(robot))
        return
        
    if robot["motion"] == Motion.turning:
        update_rack_search_turn(robot)
        return

    if robot["motion"] == Motion.stopped_for_scan:
        update_rack_scan(robot, delivery)
        return

    if robot["motion"] == Motion.follow:
        if events["new_junction"]:
            start_rack_scan(robot, delivery)
            return

        line_follow_step(sensors["S1"], sensors["S2"], 82, 20)
        return

# --- DELIVERY MODE: PICKUP HANDLER ORANGE_L --- Start when bot has finished turning INTO branch.
def update_orange_L_pickup(sensors, events, robot, delivery):
    """
    Pickup handler for orange-L rack after load has been detected.

    Called when the robot has finished turning into rack branch. 
    Next steps:
    1. Timed step forward to move closer to rack for pickup
    2. When reached: grab() called to pick up the load
    3. Timed reverse back 
    4. Turning back onto main branch with the bot facing the unloading bay at the end. 
    5. Line following until the robot has exited the rack zone (branches not detected in the last 3.5s)
    6. This code exits, dropoff code called.
    """

    state = delivery["rack_state"]

    if state == Delivery_Rack_States.approaching:
        update_rack_approach(robot, delivery)
        return

    if state == Delivery_Rack_States.reached:
        update_orange_L_reached(robot, delivery)
        return

    if state == Delivery_Rack_States.reorienting:
        update_orange_L_reorient(sensors, events, robot, delivery)
        return

    if state == Delivery_Rack_States.done:
        finish_orange_L_pickup(robot, delivery)
        return

    #print("WARNING: unknown rack_state in update_orange_L_pickup()")

# SAME FOR ALL RACKS -- NO NEED DUPLICATE
def update_rack_approach(robot, delivery):
    '''
        timed approach towards rack -- get into favourable position to grab load.
    '''
    if not robot["timed_move_started"]:
        #print("APPROACH_START")
        Red.value(1)

    done = timed_forward_step(robot, 340)

    if not done:
        return

    delivery["rack_state"] = Delivery_Rack_States.reached
    print("APPROACH_DONE -> REACHED")
    Red.value(0)

# UPDATED WITH GRABBER AND TILT
def update_orange_L_reached(robot, delivery):
    '''
        Grab the load and measure its resistance to determine load color
    '''
    print("ORANGE_L_REACHED")

    #turn_claw_up()
    grab()
    R_measure(delivery)
    print(f"RESISTOR_COLOR = {delivery['resistor_color']}")

    delivery["rack_state"] = Delivery_Rack_States.reorienting
    delivery["getout_state"] = Get_Out_of_branch.Rev_Branch
    robot["turn_dir"] = Turn_Direction.right
    robot["timed_turn_started"] = False
    robot["timed_rev_started"] = False
    robot["timed_move_started"] = False
    robot["turn_complete"] = False

    print("REACHED -> REORIENTING")

def update_orange_L_reorient(sensors, events, robot, delivery):
    '''
        Reverses the bot to allow for turning back onto main branch without the robot hitting the rack on the way out.
        When back on main branch, line following continues until rack branch is exited (no branches seen in the last 3.5s)
    '''
    state = delivery["getout_state"]

    # Step 1: Reverse until it gets to a favourable position to turn out of branch.
    if state == Get_Out_of_branch.Rev_Branch:
        update_orange_L_reverse_branch(robot, delivery)
        return

    if state == Get_Out_of_branch.Exiting_Branch:
        update_rack_exit_branch(robot, delivery)
        return

    if state == Get_Out_of_branch.RackZone:
        update_rack_leave_rack_zone(robot, sensors, events, delivery)
        return

    print("WARNING: unknown getout_state in update_orange_L_reorient()")

def finish_orange_L_pickup(robot, delivery):

    print("direction at finish is", robot["direction"])

    if robot["direction"] == Direction.acw:
        robot["gnd_loc_idx"] = 19   # OL6 re-sync hack
    elif robot["direction"] == Direction.cw:
        robot["gnd_loc_idx"] = 14 #OL1 re-sync hack

    delivery["rack_state"] = Delivery_Rack_States.approaching
    delivery["delivery_state"] = Delivery_States.unloading

    print("ORANGE_L_PICKUP_DONE | ready_for_unloading=True | node=", robot["gnd_loc_idx"])

# --- REORIENT HELPERS ---
def update_orange_L_reverse_branch(robot, delivery):
    '''
        timed reverse OUT of rack branch
    '''
    if not robot["timed_rev_started"]:
        print("REV_BRANCH_START")

    done = timed_reverse_step(robot, 1000)

    if not done:
        return

    delivery["getout_state"] = Get_Out_of_branch.Exiting_Branch
    start_turn(robot, Turn_Direction.right)

    print("REV_BRANCH_DONE -> EXITING_BRANCH")

# SAME FOR ALL RACKS BC IT DOES NOT SET TURN DIRECTION. CAN REUSE.
def update_rack_exit_branch(robot, delivery):
    '''
        carries out the turning of the bot from rack branch back onto the main branch.
    '''
    Blue.value(1)
    print("EXIT_BRANCH_TURN_START")

    robot["turn_complete"] = timed_turn_step(robot, 3500)

    if not robot["turn_complete"]:
        return

    finish_turn(robot)
    Blue.value(0)

    delivery["getout_state"] = Get_Out_of_branch.RackZone
    delivery["last_branch_time"] = ticks_ms()

    print("EXIT_BRANCH_TURN_DONE -> RACKZONE")

# SAME FOR ALL RACKS
def update_rack_leave_rack_zone(robot, sensors, events, delivery):
    ''' 
        Robot is considered to have left the rack zone if no branches have been seen in 3.5s
    '''
    if events["new_junction"]:
        delivery["last_branch_time"] = ticks_ms()
        print("RACKZONE_JUNCTION_SEEN")

    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

    if ticks_diff(ticks_ms(), delivery["last_branch_time"]) <= 3500:
        return

    print("old direction is", robot["direction"])
    print("OUT_OF_RACK_ZONE -> READY_FOR_UNLOADING")
    print("poop", target_racks[robot["target_rack_idx"]])
    if target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L:
        robot["direction"] = Direction.acw
    elif target_racks[robot["target_rack_idx"]] == Racks.rack_purple_L:
        robot["direction"] = Direction.cw
    
    print("new direction is", robot["direction"])
    delivery["getout_state"] = Get_Out_of_branch.Rev_Branch
    delivery["rack_state"] = Delivery_Rack_States.done
    print("delivery_state", delivery["rack_state"])


# --- DELIVERY MODE: PICKUP HANDLER PURPLE_L --- same as for orange_L but with some directions reversed
def update_purple_L_pickup(sensors, events, robot, delivery):
    """
    Pickup handler for orange-L rack after load has been detected.

    rack_state flow:
        approaching -> reached -> reorienting -> done

    reorienting subflow (getout_state):
        Rev_Branch -> Exiting_Branch -> RackZone
    """

    state = delivery["rack_state"]

    if state == Delivery_Rack_States.approaching:
        update_rack_approach(robot, delivery)
        return

    if state == Delivery_Rack_States.reached:
        update_purple_L_reached(robot, delivery)
        return

    if state == Delivery_Rack_States.reorienting:
        update_purple_L_reorient(sensors, events, robot, delivery)
        return

    if state == Delivery_Rack_States.done:
        finish_purple_L_pickup(robot, delivery)
        return

    print("WARNING: unknown rack_state in update_purple_L_pickup()")

# UPDATED WITH GRABBER + TILT
def update_purple_L_reached(robot, delivery):
    print("PURPLE_L_REACHED")
    #turn_claw_up()
    grab()
    R_measure(delivery)
    print(f"RESISTOR_COLOR = {delivery['resistor_color']}")

    #motor_l.Forward(speed = 0)
    #motor_r.Forward(speed = 0)
    delivery["rack_state"] = Delivery_Rack_States.reorienting
    delivery["getout_state"] = Get_Out_of_branch.Rev_Branch
    robot["turn_dir"] = Turn_Direction.left
    robot["timed_turn_started"] = False

    print("REACHED -> REORIENTING")

def update_purple_L_reorient(sensors, events, robot, delivery):
    state = delivery["getout_state"]

    # Step 1: Reverse until it gets to a favourable position to turn out of branch.
    if state == Get_Out_of_branch.Rev_Branch:
        update_purple_L_reverse_branch(robot, delivery)
        return

    if state == Get_Out_of_branch.Exiting_Branch:
        update_rack_exit_branch(robot, delivery)
        return

    if state == Get_Out_of_branch.RackZone:
        update_rack_leave_rack_zone(robot, sensors, events, delivery)
        return

    print("WARNING: unknown getout_state in update_purple_L_reorient()")
# REORIENT HELPER
def update_purple_L_reverse_branch(robot, delivery):
    if not robot["timed_rev_started"]:
        print("REV_BRANCH_START")

    done = timed_reverse_step(robot, 1000)

    if not done:
        return

    robot["motion"] = Motion.follow
    delivery["getout_state"] = Get_Out_of_branch.Exiting_Branch
    start_turn(robot, Turn_Direction.left)

    print("REV_BRANCH_DONE -> EXITING_BRANCH")

def finish_purple_L_pickup(robot, delivery):
    
    robot["gnd_loc_idx"] = 8   # PL6 re-sync hack
    delivery["rack_state"] = Delivery_Rack_States.approaching
    delivery["delivery_state"] = Delivery_States.unloading

    print("PURPLE_L_PICKUP_DONE | ready_for_unloading=True | node=8")

# --- READY FOR UNLOADING: DELIVERY MODE DROPOFF ---
def update_LHS_dropoff(sensors, events, robot, delivery):
    '''
        Called when the bot is coming from orange lower rack. Called when the robot has exited the rack zone.
        Exited when the bot has released the load into the unloading bay.
    '''
    assign_target_bay(delivery)

    if robot["motion"] == Motion.turning:
        update_unloading_turn(sensors, robot, delivery)
        return

    state = delivery["unloading_state"]

    if state == Unloading_States.finding_bay:
        update_find_unloading_entry_acw(sensors, robot, delivery)
        return

    if state == Unloading_States.counting_bays:
        update_count_bays(sensors, robot, delivery)
        return

    if state == Unloading_States.found_bay:
        update_dropoff_at_bay(sensors, events, robot, delivery)
        return

    if state == Unloading_States.done:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        delivery["delivery_state"] = Delivery_States.recover
        return

    print("WARNING: unknown unloading_state in update_LHS_dropoff()")

def update_RHS_dropoff(sensors, events, robot, delivery):
    '''
        Called when the bot is coming from purple lower rack. Called when the robot has exited the rack zone.
        Exited when the bot has released the load into the unloading bay.
    '''
    assign_target_bay(delivery)

    if robot["motion"] == Motion.turning:
        update_unloading_turn(sensors, robot, delivery)
        return

    state = delivery["unloading_state"]

    if state == Unloading_States.finding_bay:
        update_find_unloading_entry_cw(sensors, robot, delivery)
        return

    if state == Unloading_States.counting_bays:
        update_count_bays(sensors, robot, delivery)
        return

    if state == Unloading_States.found_bay:
        update_dropoff_at_bay(sensors, events, robot, delivery)
        return

    if state == Unloading_States.done:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        delivery["delivery_state"] = Delivery_States.recover
        return

    print("WARNING: unknown unloading_state in update_RHS_dropoff()")

def assign_target_bay(delivery):
    '''
        Assigns target unloading bay node based on resistor color.
    '''
    color = delivery["resistor_color"]

    if color == Resistor_Color.red:
        delivery["target_bay"] = 2
    elif color == Resistor_Color.yellow:
        delivery["target_bay"] = 1
    elif color == Resistor_Color.green:
        delivery["target_bay"] = 21
    elif color == Resistor_Color.blue:
        delivery["target_bay"] = 20
    else:
        print("WARNING: unknown resistor_color in assign_target_bay()")

def update_find_unloading_entry_acw(sensors, robot, delivery):
    '''
        Called when the bot is coming from orange_L and is travelling anticlockwise within the unloading bay.
        Triggers found_bay if the bot has reached its target bay. 
    '''
    color = delivery["resistor_color"]

    if color == Resistor_Color.blue:
        if robot["gnd_loc_idx"] == 20:
            print("BLUE_BAY_STRAIGHT_AHEAD -> FOUND_BAY")
            delivery["unloading_state"] = Unloading_States.found_bay
            return
    
        # If node 20 has not been reached yet
        line_follow_step(sensors["S1"], sensors["S2"], 82, 20)
        return

    if robot["gnd_loc_idx"] == 20:
        print("ENTER_UNLOADING_CORRIDOR")
        start_turn(robot, Turn_Direction.left)
        return
    
    # If node 20 has not been reached yet
    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

def update_find_unloading_entry_cw(sensors, robot, delivery):
    '''
        Called when the bot is coming from purple_L and is travelling clockwise within the unloading bay.
        Triggers found_bay if the bot has reached its target bay. 
    '''
    color = delivery["resistor_color"]

    if color == Resistor_Color.red:
        if robot["gnd_loc_idx"] == 2:
            print("RED_BAY_STRAIGHT_AHEAD -> FOUND_BAY")
            delivery["unloading_state"] = Unloading_States.found_bay
            return
    
        # If node 2 has not been reached yet
        line_follow_step(sensors["S1"], sensors["S2"], 82, 20)
        return

    if robot["gnd_loc_idx"] == 2:
        print("ENTER_UNLOADING_CORRIDOR")
        start_turn(robot, Turn_Direction.right)
        return
    
    # If node 2 has not been reached yet
    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

def update_count_bays(sensors, robot, delivery):
    '''
        Called when the bot reaches the target bay, starts turning into target bay.
    '''
    if robot["gnd_loc_idx"] == delivery["target_bay"]:
        print("TARGET_BAY_REACHED -> TURN_IN")
        if robot["direction"] == Direction.acw:
            turn_dir = Turn_Direction.right
        elif robot["direction"] == Direction.cw:
            turn_dir = Turn_Direction.left
        start_turn(robot, turn_dir)
        return

    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

def update_dropoff_at_bay(sensors, events, robot, delivery):
    '''
        Called when the turn into unloading bay is complete. 
        If the box is reached, stop the robot. Claw releases the load into the box.
    '''
    if events["new_T"]:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        release()   
        delivery["unloading_state"] = Unloading_States.done 
        print("BAY_REACHED -> UNLOADING_DONE")
        return

    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

def update_unloading_turn(sensors, robot, delivery):
    '''
        Carries out turning into unloading bay
    '''
    robot["turn_complete"] = timed_turn_step(robot, 1100)

    if not robot["turn_complete"]:
        return

    finish_turn(robot)

    if delivery["unloading_state"] == Unloading_States.finding_bay:
        delivery["unloading_state"] = Unloading_States.counting_bays
        print("TURN_DONE -> COUNTING_BAYS")
        return

    if delivery["unloading_state"] == Unloading_States.counting_bays:
        delivery["unloading_state"] = Unloading_States.found_bay
        print("TURN_DONE -> FOUND_BAY")
        return

    print("TURN_DONE during unexpected unloading_state")

# --- DELIVERY MODE RECOVERY: EXIT FROM BAY AFTER LOAD DROPPED OFF ---
def update_bay_recover(events, robot, delivery):
    '''
        After load is dropped off: timed reverse back to main loop spine. Turns back onto main loop spine when main spine reached.
    '''
    if not delivery["main_spine_detected"]:
        update_recover_reverse_to_spine(robot, delivery)
        return

    if robot["motion"] == Motion.turning:
        print("turning called")
        update_bay_recover_turn(robot, delivery)
        return

    print("waiting for turn -- this is what sets turn_dir")
    update_bay_recover_wait_for_junction(events, robot, delivery)

def get_bay_recover_config(delivery):
    '''
        Assigns relevant states to robot based on target rack and resistor color
    '''
    target_rack = target_racks[robot["target_rack_idx"]]

    if delivery["resistor_color"] == Resistor_Color.blue:
        if target_rack == Racks.rack_purple_L:
            return {"node": 20, "turn_dir": Turn_Direction.left,  "new_direction": Direction.acw, "turn_time_ms": 1000}
        else:
            return {"node": 20, "turn_dir": Turn_Direction.left,  "new_direction": Direction.cw,  "turn_time_ms": 2000}

    if delivery["resistor_color"] == Resistor_Color.red:
        if target_rack == Racks.rack_orange_L:
            return {"node": 2,  "turn_dir": Turn_Direction.right, "new_direction": Direction.cw,  "turn_time_ms": 1000}
        else:
            return {"node": 2,  "turn_dir": Turn_Direction.right, "new_direction": Direction.acw, "turn_time_ms": 2000}

    if delivery["resistor_color"] == Resistor_Color.green:
        if target_rack == Racks.rack_purple_L:
            return {"node": 21, "turn_dir": Turn_Direction.left,  "new_direction": Direction.acw, "turn_time_ms": 1000}
        else:
            return {"node": 21, "turn_dir": Turn_Direction.right, "new_direction": Direction.cw,  "turn_time_ms": 1000}

    if delivery["resistor_color"] == Resistor_Color.yellow:
        if target_rack == Racks.rack_orange_L:
            return {"node": 1,  "turn_dir": Turn_Direction.right, "new_direction": Direction.cw,  "turn_time_ms": 1000}
        else:
            return {"node": 1,  "turn_dir": Turn_Direction.left,  "new_direction": Direction.acw, "turn_time_ms": 1000}

    print("WARNING: unknown bay color in get_bay_recover_config()")
    return None

def update_recover_reverse_to_spine(robot, delivery):
    '''
        timed reverse back to main spine
    '''

    if not robot["timed_rev_started"]:
        print("RECOVER_REVERSE_TO_SPINE_START")

    done = timed_reverse_step(robot, 1800)

    if not done:
        return

    delivery["main_spine_detected"] = True
    print("MAIN_SPINE_DETECTED")

def update_bay_recover_wait_for_junction(events, robot, delivery):
    '''
        Starts turn back onto main spine
    '''
    cfg = get_bay_recover_config(delivery)
    if cfg is None:
        return

    # Reorienting itself on node based map.
    #robot["gnd_loc_idx"] = cfg["node"]

    # Sets motion into turning 
    start_turn(robot, cfg["turn_dir"])

    print(
        f"BAY_RECOVER_TURN_START | bay=", delivery["resistor_color"],
        f"| node={cfg['node']} | dir={cfg['turn_dir']}"
    )

def update_bay_recover_turn(robot, delivery):
    '''
        Carries out turn back onto main loop
    '''
    cfg = get_bay_recover_config(delivery)
    if cfg is None:
        return

    robot["turn_complete"] = timed_turn_step(robot, cfg["turn_time_ms"])

    if not robot["turn_complete"]:
        return

    finish_turn(robot)
    finish_bay_recover(robot, delivery, cfg)

def finish_bay_recover(robot, delivery, cfg):
    '''
        Tidies up all relevant states to eliminate stale states and mark the completion of delivery mode. 
        Sends robot back into search mode.
    '''
    robot["mode"] = Mode.search
    robot["direction"] = cfg["new_direction"]

    robot["pending_resync"] = True
    robot["pending_resync_node"] = cfg["node"]

    # Reinitialise for next time recovery is called.
    delivery["main_spine_detected"] = False
    delivery["delivery_state"] = Delivery_States.pickup
    #robot["turn_complete"] = False

    # Start pickup all over again
    delivery["search_slot_counter"] = 0
    delivery["slot_status"] = [0, 0, 0, 0, 0, 0]
    
    # Turn off all LEDs once delivery complete
    Red.value(0)
    Blue.value(0)
    Green.value(0)
    Yellow.value(0)

    print(
        f"BAY_RECOVER_DONE -> SEARCH | node={robot['gnd_loc_idx']} "
        f"| dir={robot['direction']}"
    )

def try_apply_pending_resync(sensors, robot, events):
    ''' 
        Prevents errorneous counting of nodes arising from poor alignment of robot on line after turn.
        Only allows for counting of node after the robot has properly realigned itself on line.
    '''
    if not robot["pending_resync"]:
        return

    centered = (sensors["S1"] == 1 and sensors["S2"] == 1)


    if centered and not events["on_junction"]:
        robot["gnd_loc_idx"] = robot["pending_resync_node"]
        robot["pending_resync"] = False
        robot["just_turned"] = True   # suppress next junction count
        print(f"RESYNC_APPLIED | node={robot['gnd_loc_idx']}")

# FUNCTION FOR TURNING THE PLATFORM THAT HOLDS THE CLAW, 4 wire servo
# Initialize the servo with 4 wires
servo_tilt = PWM(Pin(15)) #QN: is this pin correct? It shares the same pin as the 3 wire servo
servo_tilt.freq(50)
feedback = ADC(Pin(27)) #this is where the white wire goes -- i changed from 26 to 27 because PINOUT sheet says 27.

def turn_claw_up():
    pulse_width = 500 + (170 / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_tilt.duty_u16(duty)

def turn_claw_down():
    pulse_width = 500 + (120 / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_tilt.duty_u16(duty)

turn_claw_up()

#FUNCTION FOR MEASURING THE RESISTANCE ONCE GRABBED AND LIGHTS APPROPRITE LED UP
def R_measure(delivery):

    Red.value(0)
    Blue.value(0)
    Green.value(0)
    Yellow.value(0)

    sleep_ms(50)
    #pass current through and measure voltage V&I
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep_ms(50) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep_ms(50) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION 
    #this is the final voltage reading

    print("voltage," ,voltage)

    if voltage > 3:
        Blue.value(1) #turns LED on to blue
        delivery["resistor_color"] = Resistor_Color.blue # Blue
    elif 2.5 < voltage <= 3:
        Green.value(1)
        delivery["resistor_color"] = Resistor_Color.green # Green
    elif 1 < voltage <= 2.5:
        Red.value(1)
        delivery["resistor_color"] = Resistor_Color.red # Red
    elif 0.2 < voltage <= 1:
        Yellow.value(1)
        delivery["resistor_color"] = Resistor_Color.yellow # Yellow
    else: # if R measure doesnt work just make this the ONLY path so it delivers to green EACH TIME.
        Green.value(1)
        delivery["resistor_color"] = Resistor_Color.green # Deliver EVERYTHING to green because it is tried and tested. 
    
    #Try this out, might fix resistor color
    return delivery["resistor_color"]
    print("res color:", delivery["resistor_color"])

# --- LOCAL DELIVERY HANDLERS ---
def handle_delivery_from_orange_L(sensors, events, robot, delivery):
    if delivery["delivery_state"] == Delivery_States.pickup:
        update_orange_L_pickup(sensors, events, robot, delivery)
    elif delivery["delivery_state"] == Delivery_States.unloading:
        update_LHS_dropoff(sensors, events, robot, delivery)
    elif delivery["delivery_state"] == Delivery_States.recover:
        update_bay_recover(events, robot, delivery)

def handle_delivery_from_purple_L(sensors, events, robot, delivery):
    if delivery["delivery_state"] == Delivery_States.pickup:
        update_purple_L_pickup(sensors, events, robot, delivery)
    elif delivery["delivery_state"] == Delivery_States.unloading:
        update_RHS_dropoff(sensors, events, robot, delivery)
    elif delivery["delivery_state"] == Delivery_States.recover:
        update_bay_recover(events, robot, delivery)


# --- MODE HANDLERS
def handle_start_mode(robot, sensors):
    '''
        Getting robot out of starting box via a timed forward motion followed by turning onto main loop.
    '''
    if robot["motion"] == Motion.follow:
        robot["move_complete"] = timed_forward_step(robot, 1300)
        if robot["move_complete"]:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["motion"] = Motion.turning
            robot["turn_dir"] = Turn_Direction.left
    elif robot["motion"] == Motion.turning:
        robot["turn_complete"] = timed_turn_step(robot, 1650)
        if robot["turn_complete"]:
            robot["motion"] = Motion.follow
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["mode"] = Mode.search_init
            robot["gnd_loc_idx"] = 0
            return
        
def handle_search_init_mode(sensors, events, robot, delivery):
    '''
        Called right after start mode finishes to prevent errorneous counting of new junctions right after bot exits from box, due to some initial misalignment.
        This function gives the bot time to realign with main spine before it is allowed to count new junctions.
    '''
    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

    if events["on_junction"] or events["on_T"]:
        return

    robot["motion"] = Motion.follow
    robot["turn_complete"] = False
    robot["turn_state"] = Turn_State.start

    events["prev_on_junction"] = False
    events["prev_on_T"] = False

    robot["mode"] = Mode.search
    robot["direction"] = Direction.cw
    target_racks[robot["target_rack_idx"]] = Racks.rack_orange_L

    print("SEARCH_INIT -> SEARCH")

def handle_search_mode(sensors, events, robot, delivery):
    '''
        Handler for search mode.
    '''
    try_apply_pending_resync(sensors, robot, events)

    if robot["motion"] == Motion.turning:
        update_search_turn(sensors, robot)
        return

    if at_target_rack_zone(robot):
        rack_search(sensors, events, robot, delivery)
        return

    if should_turn_here(robot, events): # at forced turn node 2, 10, 12, 20
        start_turn(robot, get_turn_dir(robot))
        print(f"MAIN_LOOP_TURN_START | node={robot['gnd_loc_idx']} | dir={robot['turn_dir']}")
        return

    line_follow_step(sensors["S1"], sensors["S2"], 82, 20)

def update_search_turn(sensors, robot):
    '''
        timed turn during search mode 
    '''
    robot["turn_complete"] = timed_turn_step(robot, 1650)

    if not robot["turn_complete"]:
        return

    finish_turn(robot)
    print(f"MAIN_LOOP_TURN_DONE | node={robot['gnd_loc_idx']}")

def handle_delivery_mode(sensors, events, robot, delivery):
    if target_racks[robot["target_rack_idx"]] == Racks.rack_orange_L:
        handle_delivery_from_orange_L(sensors, events, robot, delivery)
        return
    elif target_racks[robot["target_rack_idx"]] == Racks.rack_purple_L:
        handle_delivery_from_purple_L(sensors, events, robot, delivery)
        return

    print("WARNING: unsupported delivery target rack")

# -- LOOP + MAPPING TEST ---
""" while True:
    update_sensors_and_events(sensors, events)

    button_now = button.value()
    ON, prev_button, last_press = handle_button(button_now, prev_button, last_press, ON)

    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        latch_events(events)
        continue
    
    if robot["mode"] not in [Mode.start, Mode.search_init]:
        update_location(robot, events)

    if robot["mode"] == Mode.start:
        handle_start_mode(robot, sensors)

    elif robot["mode"] == Mode.search_init:
        handle_search_init_mode(sensors, events, robot, delivery)
 
    else:
            
        if robot["motion"] == Motion.follow:
            if events["new_junction"] and robot["gnd_loc_idx"] in [10, 12, 20, 2]:
                start_turn(robot, Turn_Direction.left)
            elif events["new_junction"] and robot["gnd_loc_idx"] in [0]:
                start_turn(robot, Turn_Direction.right)
            line_follow_step(sensors["S1"], sensors["S2"], 82, 20)
        elif robot["motion"] == Motion.turning:
            robot["turn_complete"] = timed_turn_step(robot, 700)
            if robot["turn_complete"]:
                finish_turn(robot)     
    
        latch_events(events) """


# --- CODE RAN DURING FINAL COMPETITION TO CUT LOSSES. ---
""" robot["mode"] = Mode.start
robot["direction"] = Direction.cw
robot["gnd_loc_idx"] = 0
target_racks[robot["target_rack_idx"]] = Racks.rack_orange_L

while True:

    update_sensors_and_events(sensors, events)

    button_now = button.value()
    ON, prev_button, last_press = handle_button(button_now, prev_button, last_press, ON)

    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        latch_events(events)
        continue
    
    if robot["target_rack_idx"] != 0:
        continue
    else:
        if robot["mode"] not in [Mode.start, Mode.search_init]:
            update_location(robot, events)

        if robot["mode"] == Mode.start:
            handle_start_mode(robot, sensors)

        elif robot["mode"] == Mode.search_init:
            robot["direction"] = Direction.cw
            handle_search_init_mode(sensors, events, robot, delivery)

        elif robot["mode"] == Mode.search:
            if robot["motion"] == Motion.follow:
                if events["new_junction"] and robot["gnd_loc_idx"] in [10, 12, 20, 2]:
                    start_turn(robot, get_turn_dir(robot))
                elif events["new_junction"] and robot["gnd_loc_idx"] in [0]:
                    start_turn(robot, get_turn_dir(robot))
                
                line_follow_step(sensors["S1"], sensors["S2"], 82, 20)
            elif robot["motion"] == Motion.turning:
                robot["turn_complete"] = timed_turn_step(robot, 1450)
                if robot["turn_complete"]:
                    finish_turn(robot)     

            if at_target_rack_zone(robot):
                rack_search(sensors, events, robot, delivery)  
            
            if robot["gnd_loc_idx"] == 1:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)

        elif robot["mode"] == Mode.delivery:
            handle_delivery_from_orange_L(sensors, events, robot, delivery)


        latch_events(events)

        sleep_ms(10)    """
        

# --- FINAL MODEL --- WHAT SHOULD HAVE BEEN RUN IF NOT FOR PICO REVERSE ISSUES

while True:
    update_sensors_and_events(sensors, events)

    button_now = button.value()
    ON, prev_button, last_press = handle_button(button_now, prev_button, last_press, ON)

    if not ON:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        latch_events(events)
        continue

    if robot["mode"] not in [Mode.start, Mode.search_init]:
        update_location(robot, events)

    if robot["mode"] == Mode.start:
        handle_start_mode(robot, sensors)

    elif robot["mode"] == Mode.search_init:
        handle_search_init_mode(sensors, events, robot, delivery)

    elif robot["mode"] == Mode.search:
        handle_search_mode(sensors, events, robot, delivery)

    elif robot["mode"] == Mode.delivery:
        handle_delivery_mode(sensors, events, robot, delivery)

    else:
        print("WARNING: unknown mode")

    latch_events(events) 

#grabber test (super simple)

""" grab()
#turn_claw_down()
resistor_color=R_measure(delivery)
#turn_claw_up() """
#release() """

#Resistor identification test
grab()

color_names = {
    Resistor_Color.red: "red",
    Resistor_Color.yellow: "yellow",
    Resistor_Color.green: "green",
    Resistor_Color.blue: "blue",
    Resistor_Color.none: "none"
}

print(f"Resistor Color: {color_names.get(R_measure(), 'unknown')}")

# Broken reverse -- testing recovery only
# Start at node 19, so it turns at 20, get it to turn at 21, stop at bay, TURN 180 -- timed turn for like 2000ms? on new_junction node = 21 then left? see if doublecounting occurs. 


