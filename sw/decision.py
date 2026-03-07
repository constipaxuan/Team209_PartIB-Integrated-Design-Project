from line_following import detect_junction_type, line_follow_step, detect_junction, turn
from locations import Location, Direction, Junctions
from behaviour import Mode, Turn_Direction, Turn_State, Start_States
from lowerpurple_upper_orange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for lower purple upper orange
from upperpurple_lowerorange_R_detect import lowP_upperO_R_detect, rec_dist_laser #detection for upper purple lower orange
from LHS_dropoff import LHS_dropoff
from RHS_dropoff import RHS_dropoff
from test_motor import Motor
from utime import sleep
from main import turn_v4, Motion

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

def search_mode():
    pass

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
        
        # Step 2: Move forward. Stop when the ToF distance measurement reaches a threshold. [Insert code]

        # Step 3: Grab the load. [Insert grabber code here]

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
