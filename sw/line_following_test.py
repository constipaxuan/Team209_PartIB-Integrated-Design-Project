from test_motor import Motor
from machine import Pin
import utime

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 

S1_pin = 10
S2_pin = 11 

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)

def line_follow_step(S1_sensor, S2_sensor):
  S1 = S1_sensor.value()
  S2 = S2_sensor.value()
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

while True:
  line_follow_step(S1_sensor, S2_sensor)
  utime.sleep(0.01)