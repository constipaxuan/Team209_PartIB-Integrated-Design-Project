from test_motor import Motor
from locations import Junctions
from time import sleep



#need to map pins
#S1_pin = 
""" S2_pin = 
SL_pin = 
SR_pin =

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN) """


#move into map_state
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 



#centering code
def line_follow_step(path, S1_sensor, S2_sensor):
  S1 = S1_sensor.value()
  S2 = S2_sensor.value()
  base = 70
  corr = 40
  if path == Path.line:
    if (S1 == 0 and S2 == 1): # corrects left veer
      motor_r.Forward(speed = corr) # speed ranges from 0 to 100 as defined
      motor_l.Forward(speed = base)
    elif (S1 == 1 and S2 == 0): #corrects right veer
      motor_l.Forward(speed = corr)
      motor_r.Forward(speed = base)
    else: #centered 
      motor_r.Forward(speed = base)
      motor_l.Forward(speed = base)
    
  if detect_junction(): 
    return Path.junction
 
  return Path.line


#might want to modify so that SL and SR are taken as inputs instead. so we can easily call without having to redefine variables.
def detect_junction(prev_on_junction, SL_sensor, SR_sensor):
    SL = SL_sensor.value()
    SR = SR_sensor.value()
    if not prev_on_junction:
        return (SR == 1 or SL == 1)
    return False

def detect_junction_type(prev_on_junction, path, SL_sensor, SR_sensor):
    SL = SL_sensor.value()
    SR = SR_sensor.value()
    if not prev_on_junction:
        if path == Path.junction:
            if (SL == 1 and SR == 0): 
                return Junctions.L
            elif (SL == 0 and SR == 1):
                return Junctions.R
            elif (SL == 1 and SR == 1):
                return Junctions.RL
    return Junctions.nil
   
#Placeholders. Move to main file while loop. For testing purposes add a while loop.
path = line_follow_step(path)    
junction_type = detect_junction_type(path)

# Code for turning if it encounters a left turn or a right turn
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
  #if junction_type == Junctions.RL:
    #can decide to turn left or right
    #let it turn 180 degrees. 