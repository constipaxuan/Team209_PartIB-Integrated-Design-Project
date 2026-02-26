#this code is NOT functional. Handling logic right now but eventiually it WILL be pipelined and not stuck in this monstrosity of blocking while loops.
from line_following import detect_junction_type, line_follow_step, detect_junction
from locations import Location, Unloading_States, Direction, Path, Junctions
from behaviour import Mode

location = Location.start
unloading_states = Unloading_States.none
direction = Direction.cw
mode = Mode.start

path = Path.line
upstairs = False


#read sensors here
#SL = 
#SR =

def mapping(previous_state, SL, SR):
    if previous_state == Location.unloading and mode != Mode.delivery and upstairs == False:
        if direction == Direction.cw and detect_junction_type(path) == Junctions.R: 
            location = Location.

branch_count = 0
unloading_state = 0 #check if this is acceptable. Zero again once outside unloading zone.
def unloading_zone():
    if mode == Mode.search or mode == Mode.delivery:
        if (branch_count == 0 and SR == 1):
            unloading_state = Unloading_States.red
            branch_count += 1
        elif (branch_count == 1 and SR == 1):
            unloading_state = Unloading_States.yellow
            branch_count += 1
        elif (branch_count == 2 and SR == 1):
            unloading_state = Unloading_States.none
            branch_count += 1
        elif (branch_count == 3 and SR == 1):
            unloading_state = Unloading_States.green
            branch_count += 1
        elif (branch_count == 4 and SR == 1):
            unloading_state = Unloading_States.blue
            branch_count += 1

        if (branch_count == 0 and SL == 1):
            unloading_state = Unloading_States.blue
            branch_count += 1
        elif (branch_count == 1 and SL == 1):
            unloading_state = Unloading_States.green
            branch_count += 1
        elif (branch_count == 2 and SL == 1):
            unloading_state = Unloading_States.none
            branch_count += 1
        elif (branch_count == 3 and SL == 1):
            unloading_state = Unloading_States.yellow
            branch_count += 1
        elif (branch_count == 4 and SL == 1):
            unloading_state = Unloading_States.red
            branch_count += 1
        elif branch_count == 5 and rotate

def rack_zone():
    if direction == Direction.cw:




while True:
    #read sensors here
    #SL = 
    #SR = 
    while (in_elevator == False and upstairs == False): # while downstairs
        if (SL and SR == True): #encountered + shape
            cross = True
            while (SL ^ SR == False): #+ or line. Need to check whether it instantly deactivates upon running into L or R junctions.
                if SL == True:
                    cross = False
                    acw = True
                    cw = False
                    unloading_zone = False
                elif SR == True:
                    cross = False
                    acw = False
                    cw = True
                    unloading_zone = False
    
        while cw:
            # The below code handles enter and exit of the lower elevator zone.
            if (orange_rack == True and cross == True) :
                orange_rack = False
                elevator_low = True
            elif (elevator_low == True and cross == True): #need to define elevator function
                purple_rack = True
                elevator_low = False
        
            while purple_rack == True: # potential issues: 6th branch not recognised, considered unloading zone. 
                #Currently the solution to that is that under a while True loop we will have if purple_rack then call the rack function that runs until 6 branches r cleared. 
                #Bot will enter and exit multiple times though, need to make sure function doesn't get called more than once. Can add a running variable that stops that.
                while rack_branch_count < 6:
                    if (SR ^ SL == True): # by right it is SR = True
                        rack_branch_count += 1
                rack_branch_count = 0
                unloading_zone = True
                purple_rack = False
            
        
            #fill in later
            while orange_rack:
                pass
            
            while unloading_zone:
                #Red Yellow Green Blue






        while acw:
            # The below code handles enter and exit of the lower elevator zone.
            if (elevator_low == True and cross == True):
                orange_rack = True
                elevator_low = False
            elif (purple_rack == True and cross == True):
                elevator_low = True
                purple_rack = False
            
            while orange_rack == True:
                while rack_branch_count < 6:
                    if (SR ^ SL == True): # by right it is SL = True
                        rack_branch_count += 1
                rack_branch_count = 0
                unloading_zone = True
                orange_rack = False
            
            #fill in later
            while purple_rack:
                pass


       




         
