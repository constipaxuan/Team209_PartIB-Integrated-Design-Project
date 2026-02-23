from test_motor import Motor

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 

base = 70
corr = 40

while True: 
  #read sensors here
  #S1 = 
  #S2 = 

  if (S1 == 0 and S2 == 1): # corrects left veer
    motor_r.Forward(speed = corr) # speed ranges from 0 to 100 as defined
    motor_l.Forward(speed = base)
  elif (S1 == 1 and S2 == 0): #corrects right veer
    motor_l.Forward(speed = corr)
    motor_r.Forward(speed = base)
  else: #centered 
    motor_r.Forward(speed = base)
    motor_l.Forward(speed = base)
