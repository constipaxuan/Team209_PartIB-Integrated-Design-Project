#import utime

from machine import Pin, PWM
from utime import sleep, sleep_ms
#from enum import Enum
#from map_state import mapping
#from locations import Location, Direction


class Mode():
    start = 0
    search = 1
    delivery = 2

class Motion():
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

class Junctions():
    R = 1
    L = 2
    RL = 3
    nil = 4

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
#direction = Direction.acw

#centering code
def line_follow_step(S1, S2):
  base = 70
  corr = 40
  
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


def turn(junction_type):
  base = 70
  if junction_type == Junctions.L:
    motor_l.Reverse(speed = 50)
    motor_r.Forward(speed = 50)
    sleep(1) # might need to adjust time depending on how long it takes to turn 90 degrees. Might also want to add some sort of feedback system to determine when to stop turning instead of just relying on time.
    motor_l.Forward(speed = base)
    motor_r.Forward(speed = base)
# turn line following off while turning
  elif junction_type == Junctions.R:
    motor_l.Forward(speed = 50)
    motor_r.Reverse(speed = 50)
    sleep(1) # might need to adjust time depending on how long it takes to turn 90 degrees. Might also want to add some sort of feedback system to determine when to stop turning instead of just relying on time.
    motor_l.Forward(speed = base)
    motor_r.Forward(speed = base)
  elif junction_type == Junctions.RL:
    #arbitrarily making it turn right now. will change later. 
    motor_l.Forward(speed = 50)
    motor_r.Reverse(speed = 50)
    sleep(1) # might need to adjust time depending on how long it takes to turn 90 degrees. Might also want to add some sort of feedback system to determine when to stop turning instead of just relying on time.
    motor_l.Forward(speed = base)
    motor_r.Forward(speed = base) 


def update_start_T_count(SL, SR):
    global start_T_shape_count, counting
    if SL == 1 and SR == 1 and counting:
        start_T_shape_count += 1
        counting = False # Latch on
        print(f"Junction Detected! Total: {start_T_shape_count}")
    elif SL == 0 and SR == 0:
        counting = True # Ready for next junction

def get_out_of_box(SL, SR):
    # --- Main Mission Loop ---
    base = 70
    while True:

        S1 = S1_sensor.value()
        S2 = S2_sensor.value()
        SL = SL_sensor.value()
        SR = SR_sensor.value()

        update_start_T_count(SL, SR)
        
        # State 1: Drive out of the box, drive straight
        if start_T_shape_count < 2:
            line_follow_step(S1, S2)

        # State 2: Hit second T shape, turn clockwise
        elif start_T_shape_count == 2:
            print("Turning Clockwise into corridor...")
            motor_l.Forward(base)
            motor_r.Reverse(base)
            sleep_ms(600) # Adjust this time so it clears the T-junction
            line_follow_step(S1, S2)
            start_T_shape_count = 2.1 # Increment to avoid re-triggering this state
            
        # State 3: Hit third T shape, turn anti-clockwise
        elif start_T_shape_count > 3:
            print("Turning Anti-clockwise into rack...")
            motor_l.Reverse(base)
            motor_r.Forward(base)
            sleep_ms(600)
            line_follow_step(S1, S2)
            print("Arrived at the Purple Rack.")
            break # Exit this navigation loop to start scanning


while True:
    S1 = S1_sensor.value()
    S2 = S2_sensor.value()
    SL = SL_sensor.value()
    SR = SR_sensor.value()

    on_junction = (SL == 1 or SR == 1)
    new_junction = (not prev_on_junction) and on_junction

    if mode == Mode.start:
       get_out_of_box(SL, SR)
       mode = Mode.search
    else:
        if motion == Motion.follow:
            if new_junction:
                sleep(0.05)
                SL = SL_sensor.value()
                SR = SR_sensor.value()
                junction_type = detect_junction_type(SL, SR)
                motion = Motion.turning
            else:
                line_follow_step(S1, S2)
        elif motion == Motion.turning:
            turn(junction_type)
            motion = Motion.follow
        prev_on_junction = on_junction

