from main import sensors, events, robot, delivery, Motion
from locations import Direction


# List of junctions/nodes on lower floor MAIN LOOP (Increasing in ACW direction):
'''
1. Starting node
2. Yellow bay
3. Red bay
4. PL1
5. PL2
6. PL3
7. PL4
8. PL5
9. PL6
10. Purple T
11. Elevator low P
12. Elevator junction
13. Elevator low O
14. Orange T
15. OL1
16. OL2
17. OL3
18. OL4
19. OL5
20. OL6
21. Blue bay
22. Green bay
'''

class Node:
    Starting_node = 0
    Yellow_bay = 1
    Red_bay = 2
    PL1 = 3
    PL2 = 4
    PL3 = 5
    PL4 = 6
    PL5 = 7
    PL6 = 8
    Purple_T = 9
    Elev_low_P = 10
    Elev_junc = 11
    Elev_low_O = 12
    Orange_T = 13
    OL1 = 14
    OL2 = 15
    OL3 = 16
    OL4 = 17
    OL5 = 18
    OL6 = 19
    Blue_bay = 20
    Green_bay = 21

lower_loop = [Node.Starting_node, Node.Yellow_bay, Node.Red_bay, 
         Node.PL1, Node.PL2, Node.PL3, Node.PL4, Node.PL5, Node.PL6, Node.Purple_T, 
         Node.Elev_low_P, Node.Elev_junc, Node.Elev_low_O,
         Node.Orange_T, Node.OL1, Node.OL2, Node.OL3, Node.OL4, Node.OL5, Node.OL6,
         Node.Blue_bay, Node.Green_bay]


N = len(lower_loop)

# at 2nd T junction: gnd_loc_idx = 0

if events["new_junction"] and robot["motion"] == Motion.follow:
    if robot["direction"] == Direction.acw:
        gnd_loc_idx = (robot["gnd_loc_idx"] + 1) % N
    if robot["direction"] == Direction.cw:
        gnd_loc_idx = (robot["gnd_loc_idx"] - 1) % N

# 0 means uncleared, 1 means cleared
cleared_status = {
    Node.PL1 : 0,
    Node.PL2 : 0,
    Node.PL3 : 0,
    Node.PL4 : 0,
    Node.PL5 : 0,
    Node.PL6 : 0,
    Node.OL1 : 0,
    Node.OL2 : 0,
    Node.OL3 : 0,
    Node.OL4 : 0,
    Node.OL5 : 0,
    Node.OL6 : 0
}

def get_out_of_box(sensors, events, robot, delivery):
    # --- Main Mission Loop ---

    # To prevent double counting: Only can update count while NOT in turning mode.
    if robot["start_state"] == Start_States.start or robot["start_state"] == Start_States.turn1_done:
        events["start_T_shape_count"] = update_start_T_count(events["start_T_shape_count"], events["new_T"])

    if robot["start_state"] == Start_States.start:   
    # State 1: Drive out of the box, drive straight
    #if start_T_shape_count < 2:
        if events["start_T_shape_count"] == 2:
            if sensors["SL"] == 0 and sensors["SR"] == 0: # Move forward until the SL and SR lose the white line. 
                Blue.value(1)
                robot["start_state"] = Start_States.turn1
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
                robot["turn_state"] = Turn_State.start
                robot["turn_complete"] = False

        else:
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    # State 2: Hit second T shape, turn clockwise
    elif robot["start_state"] == Start_States.turn1:

        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.right, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if  robot["turn_complete"]:
            robot["start_state"] = Start_States.turn1_done
            #print("turn 1 done")
    
    elif robot["start_state"] == Start_States.turn1_done:
        if events["start_T_shape_count"] == 3:
            robot["start_state"] = Start_States.turn2
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            Blue.value(1)

        else:
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)

    elif robot["start_state"] == Start_States.turn2:
        if not robot["turn_complete"]:
            robot["turn_state"], robot["turn_complete"] = turn_v4(Turn_Direction.left, sensors["S1"], sensors["S2"], robot["turn_state"], motor_l, motor_r)
        if robot["turn_complete"]:
            #print("turn 2 COMPLETED")
            robot["start_state"] = Start_States.turn2_done
            delivery["target_rack"] = Location.rack_purple_L
            robot["turn_complete"] = False
            robot["turn_state"] = Turn_State.start
            Blue.value(0)
            line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
            
    
    elif robot["start_state"] == Start_States.turn2_done:
        line_follow_step(sensors["S1"], sensors["S2"], 80, 20)
        robot["mode"] = Mode.search_init
        robot["location"] = Location.rack_purple_L
        #print("turn 2 done")


