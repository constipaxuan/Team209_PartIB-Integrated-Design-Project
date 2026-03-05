#import utime

from machine import Pin, PWM
from utime import sleep, sleep_ms
#from enum import Enum
from behaviour import Turn_Direction, Turn_State, Mode, Start_States
from locations import Junctions

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

    def Reverse(self, speed=30):
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

prev_on_junction = False
new_junction = False
motion = Motion.follow
mode = Mode.start
counting = True
start_T_shape_count = 0
junction_type = Junctions.nil
turn_dir = Turn_Direction.nil
turn_state = Turn_State.turn_search
start_state = Start_States.start

#centering code
def line_follow_step(S1, S2, base, corr):

  if (S1 == 0 and S2 == 1): # corrects left veer
    motor_r.Forward(speed = corr) # speed ranges from 0 to 100 as defined
    motor_l.Forward(speed = base)
  elif (S1 == 1 and S2 == 0): #corrects right veer
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



# Assumes that the turning of the car is wide enough such that the front aligns with line before the back
'''
    turn_search: Has yet to see line. If turning left: When S1 = 1, line is crossed, turn_state = turn_cross
    turn_cross: Has seen line, sensor that seen line has yet to unsee. When S1 unsees line the bot is in a safe geometry to start line following
    done: S1 has unseen the line. Start line following. End when fully aligned.
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
                motor_l.Forward(speed = 30)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if (S1 == 1 and S2 == 0):
                turn_state = Turn_State.turn_cross
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 30)
        
        return False, turn_state

    
    # Want outer sensor to lose the line again -- this is half_done state.
    if turn_state == Turn_State.turn_cross:
        if turn_dir == Turn_Direction.left:
            if S2 == 0:
                turn_state = Turn_State.half_done
            else:
                motor_l.Forward(speed = 30)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if S1 == 0:
                turn_state = Turn_State.half_done
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 30)
        
        return False, turn_state
    
    # Stop when outer sensor reacquires the line -- transition to done state
    if turn_state == Turn_State.half_done:
        if turn_dir == Turn_Direction.left:
            if S2 == 1:
                turn_state = Turn_State.done
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 30)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if S1 == 1:
                turn_state = Turn_State.done
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 30)
        
        return False, turn_state
    
    if turn_state == Turn_State.done:
        if not (S1 == 0 and S2 == 0):
            line_follow_step(S1, S2, 60, 10)
            return False, turn_state
        if (S1 == 0 and S2 == 0):
            return True, Turn_State.turn_search
            

            


def turn_v2(turn_dir, S1, S2, turn_state):
    
    if turn_state == Turn_State.turn_search:
        #still trying to find the line
        if turn_dir == Turn_Direction.left:
            motor_l.Forward(speed = 50)
            motor_r.Forward(speed = 0)
            if S1 == 1:
                turn_state = Turn_State.turn_cross
                #motor_l.Forward(speed = 0) # stops when it has seen the line.
                #motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 50)
            if S2 == 1:
                turn_state = Turn_State.turn_cross
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)
            
        return False, turn_state
    
    #Has found the line.
    if turn_state == Turn_State.turn_cross:
        if turn_dir == Turn_Direction.left:
            if S1 == 0:
                turn_state = Turn_State.half_done
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)
            else:
                motor_l.Forward(speed = 50)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if S2 == 0:
                turn_state = Turn_State.half_done  
                #motor_l.Forward(speed = 0)
                #motor_r.Forward(speed = 0)   
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 50)  
        return False, turn_state

    if turn_state == Turn_State.half_done:
    
        if turn_dir == Turn_Direction.left:
            if (S1 == 0 and S2 == 1):
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                turn_state = Turn_State.done
            else:
                motor_l.Forward(speed = 50)
                motor_r.Forward(speed = 0)
        elif turn_dir == Turn_Direction.right:
            if (S1 == 1 and S2 == 0):
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                turn_state = Turn_State.done     
            else:
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 50)  
        return False, turn_state

    if turn_state == Turn_State.done:
        if not (S1 == 0 and S2 == 0):
            line_follow_step(S1, S2, 60, 0)
            return False, turn_state
        if (S1 == 0 and S2 == 0):
            return True, Turn_State.turn_search
        

# turn_complete, seen_line = turn_v2(turn_dir, S1, S2, turn_state)

def update_start_T_count(SL, SR, start_T_shape_count, counting):
    #global start_T_shape_count, counting
    if SL == 1 and SR == 1 and counting:
        start_T_shape_count += 1
        counting = False # Latch on
    elif SL == 0 and SR == 0:
        counting = True # Ready for next junction
    
    return start_T_shape_count, counting

# Call this in discrete time steps while mode = Mode.start
def get_out_of_box(S1, S2, SL, SR, start_T_shape_count, counting, turn_complete, turn_state, start_state, mode):
    # --- Main Mission Loop ---

    # To prevent double counting: Only can update count while NOT in turning mode.
    if start_state == Start_States.start or start_state == Start_States.turn1_done:
        start_T_shape_count, counting = update_start_T_count(SL, SR, start_T_shape_count, counting)

    if start_state == Start_States.start:   
        # State 1: Drive out of the box, drive straight
    #if start_T_shape_count < 2:
        if start_T_shape_count == 2:
            start_state = Start_States.turn1
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            turn_state = Turn_State.turn_search
            turn_complete = False
        else:
            line_follow_step(S1, S2, 60, 20)

        return start_T_shape_count, counting, start_state, turn_complete, turn_state, mode

    # State 2: Hit second T shape, turn clockwise
    if start_state == Start_States.turn1:

        if not turn_complete:
            turn_complete, turn_state = turn_v3(Turn_Direction.right, S1, S2, turn_state)
        if turn_complete:
            start_state = Start_States.turn1_done

        return start_T_shape_count, counting, start_state, turn_complete, turn_state, mode
    
    if start_state == Start_States.turn1_done:
        if start_T_shape_count == 3:
   
            start_state = Start_States.turn2
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            turn_state = Turn_State.turn_search
            turn_complete = False
        else:
            line_follow_step(S1, S2, 60, 20)
        
        return start_T_shape_count, counting, start_state, turn_complete, turn_state, mode

    if start_state == Start_States.turn2:
        if not turn_complete:
            turn_complete, turn_state = turn_v3(Turn_Direction.left, S1, S2, turn_state)
        if turn_complete:
            start_state = Start_States.turn2_done
            turn_complete = False
            turn_state = Turn_State.turn_search

        return start_T_shape_count, counting, start_state, turn_complete, turn_state, mode
    
    if start_state == Start_States.turn2_done:
        line_follow_step(S1, S2, 60, 20)
        mode = Mode.search
        return start_T_shape_count, counting, start_state, turn_complete, turn_state, mode

class Test_Corners:
    upper_right = 1
    upper_left = 2
    unloading = 3
    back_to_start = 4

turn_complete = False
turn_state = Turn_State.turn_search
take_next_turn = False
# test_corner is the next corner to be turned.
test_corner = Test_Corners.upper_right
OB_counter = 0

def test_main_loop(SL, SR, test_corner, take_next_turn, OB_counter, turn_dir, new_junction):
    if test_corner == Test_Corners.upper_right:
        if (SL == 1 and SR == 1) and new_junction:
            take_next_turn = True
            turn_dir = Turn_Direction.left
    if test_corner == Test_Corners.upper_left:
        if (SL == 1) and new_junction:
            take_next_turn = True
            turn_dir = Turn_Direction.left
    if test_corner == Test_Corners.unloading:
        if OB_counter == 6:
            take_next_turn = True
            turn_dir = Turn_Direction.left
            OB_counter = 0
        else:
            if (SL == 1 and SR == 1) and new_junction:
                OB_counter = 0
            elif (SL == 1 and SR == 0) and new_junction:
                OB_counter += 1
            take_next_turn = False
    if test_corner == Test_Corners.back_to_start:
        if (SR == 1 and SL == 0) and new_junction:
            take_next_turn = True
            turn_dir = Turn_Direction.right
    
    return test_corner, take_next_turn, OB_counter, turn_dir, new_junction


corners = [
    Test_Corners.upper_right,
    Test_Corners.upper_left,
    Test_Corners.unloading,
    Test_Corners.back_to_start
]

corner_idx = 0

while True:
    S1 = S1_sensor.value()
    S2 = S2_sensor.value()
    SL = SL_sensor.value()
    SR = SR_sensor.value()

    on_junction = (SL == 1 or SR == 1)
    new_junction = (not prev_on_junction) and on_junction

    if mode == Mode.start:
       start_T_shape_count, counting, start_state, turn_complete, turn_state, mode = get_out_of_box(S1, S2, SL, SR, start_T_shape_count, counting, turn_complete, turn_state, start_state, mode)
    else:
        test_corner, take_next_turn, OB_counter, turn_dir, new_junction = test_main_loop(SL, SR, test_corner, take_next_turn, OB_counter, turn_dir, new_junction)

        if motion == Motion.follow:
            if take_next_turn == True and new_junction:
                SL = SL_sensor.value()
                SR = SR_sensor.value()
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                junction_type = detect_junction_type(SL, SR)
                motion = Motion.turning
                turn_state = Turn_State.turn_search
                turn_complete = False
            else:
                line_follow_step(S1, S2, 60, 20)

        if motion == Motion.turning:
            if not turn_complete:
                turn_complete, turn_state = turn_v3(turn_dir, S1, S2, turn_state)
                
            else:
                motion = Motion.follow
                turn_complete = False
                turn_state = Turn_State.turn_search
                if corner_idx < len(corners) - 1:
                    corner_idx += 1
                else:
                    corner_idx = 0
                    sleep_ms(500)
                    motor_l.Forward(speed = 0)
                    motor_r.Forward(speed = 0)
                test_corner = corners[corner_idx]
                take_next_turn = False
  
    prev_on_junction = on_junction


