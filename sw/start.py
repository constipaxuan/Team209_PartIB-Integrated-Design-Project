from test_motor import Motor
from machine import Pin
from utime import sleep_ms

speed = 50
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=6, PWMPin=7) 
counting = True

def update_start_T_count():
    while True:
        if SL == 1 and SR == 1 and counting:
            start_T_shape_count += 1
            counting = False # Latch on
        elif SL == 0 and SR == 0:
                counting = True # Ready for next junction

# drive forwards out of the starting box, just drive straight
while True:
    update_start_T_count()
    # State 1: Drive out of the box, drive straight
    if start_T_shape_count < 2:
        motor_l.Forward(speed)
        motor_r.Forward(speed)

    # State 2: Hit second T shape, turn clockwise
    elif start_T_shape_count == 2:
    # Once hit second T shape, turn clockwise. Turn clockwise code below
    # drive straight

    elif start_T_shape_count == 3:
    # Once hit third T shape, turn anti-clockwise. Turn anti-clockwise code below
    # drive straight