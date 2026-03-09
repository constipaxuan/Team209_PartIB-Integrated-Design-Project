from line_following import detect_junction_type, line_follow_step, detect_junction, turn
from locations import Location, Direction, Junctions
from behaviour import Mode, Turn_Direction, Turn_State, Start_States
from lowerpurple_upper_orange_R_detect import * #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import * #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff
from test_motor import Motor
from utime import sleep
from main import SR_sensor, turn_v4, Motion
from R_pickup_N_measure import Pgram_tilt, grab, R_measure #variables & functions for R measurement and pickup

location = Location.start
direction = Direction.cw
mode = Mode.start
turn_complete = False
turn_state = Turn_State.start
motion = Motion.follow
rack_junction_reached = False

#shld be defined in main code
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 


# For testing purposes: make it turn at every junction (maybe R if RL detected?) Just to make sure our junction detection logic works.
#def take_a_turn(junction_event):
#    return junction_event

#def mode_tracker():
#    pass

#def start_mode():
#    pass

def search_mode(location):
    # I assume that this function is called when the bot should turn on the side sensor, I assume that the bot is already at the rack positions
    if location in [Location.rack_orange_U, Location.rack_purple_L]:
        if slot_status.count(1) < 6: #number of cleared slots is less than 6
            lowP_upperO_R_detect() #this keeps on running until the rack is cleared
            if R_detected:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay
    else:
        if slot_status.count(1) < 6: #number of cleared slots is less than 6
            upperP_lowO_R_detect() #this keeps on running until the rack is cleared
            if R_detected:
                # INSERT code to swap to delivery mode to pick up resistor and drop off at bay (The else error above will go away once this function is added)

def delivery_mode(S1, S2, location, direction, junction_type, new_junction, resistor_color, turn_state, turn_complete):
    base = 70
    # Step 1: Enter delivery mode when laser detects a resistor load while bot is on a branch. 
    if location == Location.rack_orange_L:
        if new_junction and motion != Motion.turning:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            motion = Motion.turning
            turn_state = Turn_State.start
            if direction == Direction.cw:
                turn_dir = Turn_Direction.right
            elif direction == Direction.acw:
                turn_dir = Turn_Direction.left
        
        if motion == Motion.turning:
            if not turn_complete:
                turn_state, turn_complete = turn_v4(turn_dir, S1, S2, turn_state)
            else:
                motion = Motion.follow
                turn_complete = False
                turn_state = Turn_State.start
        
        #Step 2: Move forward closer to resistor
        motor_l.Forward(speed = base)
        motor_r.Forward(speed = base)
        sleep(0.5) # might need to adjust time 
        motor_l.Forward(speed = 0)
        motor_r.Forward(speed = 0)

        # Step 3: Grab the load. [Insert grabber code here]
        grab() 
        R_measure(resistor_color) #measure the resistor color and store it as a variable so that the bot knows which bay to drop it off at
        # Step 4: Reverse until RL junction is detected. Then turn right towards the drop off bay.

        #move forward until you grab. After grabbing reverse until reach RL junction, turn 90 deg right (cw)
        if rack_junction_reached == False:
            motor_l.Reverse(speed = 60)
            motor_r.Reverse(speed = 60)

        if new_junction and junction_type == Junctions.RL:
            rack_junction_reached = True
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            motion = Motion.turning
            turn_state = Turn_State.start
            turn_dir = Turn_Direction.right
            direction = Direction.acw

            if motion == Motion.turning:
                if not turn_complete:
                    turn_v4(Turn_Direction.right, S1, S2, turn_state)
                motion = Motion.follow
                turn_complete = False
                turn_state = Turn_State.start
        
        #rack_branches_OL is known
        while memory["rack_branches_OL"] % 6 != 0:
            if junction_type == Junctions.L:
                memory["rack_branches_OL"] -= 1

        LHS_dropoff(resistor_color)
        #enter unloading bay with blue closest
        # LHS dropoff stops when load has been deposited
        # reverse until reach RL junction. turning direction depends on where u wanna go next -- handled by search decision?
        motor_l.Forward(base)
        motor_r.Forward(base)
        sleep(0.5)
        while junction_type != Junctions.RL:
            # exit this loop when T junction is detected.
            line_follow_step(S1, S2)
        #decide to turn left or right depending on which rack it wants to go to.
    
    elif location == Location.rack_purple_L:
    #copy and paste later
        pass