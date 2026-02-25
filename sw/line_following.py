from test_motor import Motor
from machine import Pin
from locations import Path, Junctions

path = Path.line

#need to map pins
S1_pin = 
S2_pin = 
SL_pin = 
SR_pin =

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 

base = 70
corr = 40

#centering code
def line_follow_step(path):
  S1 = S1_sensor.value()
  S2 = S2_sensor.value()
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

def detect_junction():
    SL = SL_sensor.value()
    SR = SR_sensor.value()
    return (SR == 1 or SL == 1)

def detect_junction_type(path):
    SL = SL_sensor.value()
    SR = SR_sensor.value()
    if path == Path.junction:
        if (SL == 1 and SR == 0): 
            return Junctions.L
        elif (SL == 0 and SR == 1):
            return Junctions.R
        elif (SL == 1 and SR == 1):
            return Junctions.RL

#Placeholders. Move to main file while loop. For testing purposes add a while loop.
path = line_follow_step(path)    
junction_type = detect_junction_type(path)

