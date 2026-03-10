from main import turn_v4, line_follow_step, back_line_follow_step, detect_junction_type, turn_180
from behaviour import Turn_Direction, Turn_State
from machine import Pin
from test_motor import Motor

# Start in front of a LEFT turn.
# Test for 90 deg turn

prev_on_junction = False
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
motor_r = Motor(dirPin=7, PWMPin=6) 


while True:
    S1 = S1_sensor.value()
    S2 = S2_sensor.value()
    SL = SL_sensor.value()
    SR = SR_sensor.value()

    on_junction = (SL == 1 or SR == 1)
    new_junction = (not prev_on_junction) and on_junction

    if new_junction and not turning:
        if (SL == 0 and SR == 0): # move forward until we lose the white line.
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            turning = True
    
    if turning:
        turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state, motor_l, motor_r)

        if turn_complete:
            turning = False
            turn_complete = False
            turn_state = Turn_State.start
    else:
        line_follow_step(S1, S2, 60, 20)

    prev_on_junction = on_junction 

""" # Test for 180 deg turn
while True: 
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

    if turning:
        if not turn_complete:
            turn_state, turn_complete, turn_phase = turn_180(Turn_Direction.left, S1, S2, turn_state, turn_phase, motor_l, motor_r)
        else:
            turning = False
            turn_complete = False
            turn_state = Turn_State.start
    elif not turning:
        back_line_follow_step(S1, S2, 60, 20)

    prev_on_junction = on_junction """