#import utime

from machine import Pin, PWM
from time import sleep, sleep_ms, ticks_ms, ticks_diff
#from enum import Enum
from behaviour import Turn_Direction, Turn_State, Mode, Start_States, TNT_states
from locations import Junctions, Location, Direction
from decision import sensors, robot, events, delivery
from map_state import mapping, memory


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

button = Pin(14, Pin.IN) # button is a PULL_DOWN so it reads 0 when not pressed and 1 when pressed.

# STOP IMMEDIATELY AFTER RESET
motor_l.Forward(0)
motor_r.Forward(0)

ON = False
prev_button = 0

prev_on_junction = False
new_junction = False
motion = Motion.follow
mode = Mode.start
counting = True
start_T_shape_count = 0
junction_type = Junctions.nil
turn_dir = Turn_Direction.nil
turn_state = Turn_State.start
start_state = Start_States.start
location = Location.start
direction = Direction.acw

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
  base = 70
  corr = 40
  
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
        events["start_T_shape_count"] = update_start_T_count(sensors["SL"], sensors["SR"], events["start_T_shape_count"], events["new_T"])

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

turn_complete = False
turn_state = Turn_State.start
take_next_turn = False
# test_corner is the next corner to be turned.
test_corner = Test_Corners.upper_right
OB_counter = 0
last_press = 0
tnt_state = TNT_states.nil

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

""" prev_on_junction = False
turn_state = Turn_State.start
turn_dir = Turn_Direction.left
turn_complete = False
turning = False
turn_phase = 0

S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6)  """

# --- TURN TEST ---
""" while True:
    S1 = S1_sensor.value()
    S2 = S2_sensor.value()
    SL = SL_sensor.value()
    SR = SR_sensor.value()

    on_junction = (SL == 1 or SR == 1)
    new_junction = (not prev_on_junction) and on_junction

    if new_junction and not turning:
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)
        turning = True
        Blue.value(1)
    
    if turning:
        turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)

        if turn_complete:
            turning = False
            turn_complete = False
            turn_state = Turn_State.start
            Blue.value(0)
    else:
        line_follow_step(S1, S2, 80, 20)

    prev_on_junction = on_junction   """

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

    if events["new_junction"]:
        events["junction_type"] = detect_junction_type(memory["prev_on_junction"], sensors["SL"], sensors["SR"])
    else:
        events["junction_type"] = Junctions.nil
    
    robot["location"] = mapping(events["previous_state"], robot["mode"], robot["direction"], events["junction_type"])


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
                        sleep_ms(500)
                        motor_l.Forward(speed = 0)
                        motor_r.Forward(speed = 0)
                    test_corner = corners[corner_idx]
                    
    
        events["prev_on_junction"] = events["on_junction"]
        events["prev_on_T"] = events["on_T"]  """



# Assumes that the turning of the car is wide enough such that the front aligns with line before the back
'''
    turn_search: Has yet to see line. If turning left: When S1 = 1, line is crossed, turn_state = turn_cross
    turn_cross: Has seen line, sensor that seen line has yet to unsee. When S1 unsees line the bot is in a safe geometry to start line following
    done: S1 has unseen the line. Start line following. End when fully aligned.
'''
'''
def turn_v3(turn_dir, S1, S2, turn_state):
    if turn_state == Turn_State.turn_search:
        #Stop when S1 and S2 straddle the line.
        if turn_dir == Turn_Direction.left:
            if (S1 == 0 and S2 == 1):
                turn_state = Turn_State.turn_cross
                motor_l.Forward(speed = 0) # stops when it has seen the line.
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 60)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if (S1 == 1 and S2 == 0):
                turn_state = Turn_State.turn_cross
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 60)
        
        return False, turn_state

    
    # Want outer sensor to lose the line again -- this is half_done state.
    if turn_state == Turn_State.turn_cross:
        if turn_dir == Turn_Direction.left:
            if S2 == 0:
                turn_state = Turn_State.half_done
            else:
                motor_l.Forward(speed = 60)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if S1 == 0:
                turn_state = Turn_State.half_done
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 60)
        
        return False, turn_state
    
    # Stop when outer sensor reacquires the line -- transition to done state
    if turn_state == Turn_State.half_done:
        if turn_dir == Turn_Direction.left:
            if S2 == 1:
                turn_state = Turn_State.done
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 60)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if S1 == 1:
                turn_state = Turn_State.done
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 60)
        
        return False, turn_state
    
    if turn_state == Turn_State.done:
        if not (S1 == 0 and S2 == 0):
            line_follow_step(S1, S2, 60, 20)
            return False, turn_state
        if (S1 == 0 and S2 == 0):
            return True, Turn_State.turn_search '''