# if the car comes down from the right hand side to the lloading bay
# Red = 0, Yellow = 1, SKIP the starting box = 2, Green = 3, Blue = 4
target_bay = 0 
drop_off_bay = 0
counting_line = False # This is our "latch"
dropped_off = False # This is to prevent the car from dropping off multiple times after reaching the target bay
def RHS_dropoff():
    if resistor_color == 0: 
        target_bay = 0 # Red
    if resistor_color == 1: 
        target_bay = 1 # Yellow
    if resistor_color == 3: 
        target_bay = 3 # Green
    if resistor_color == 4: 
        target_bay = 4 # Blue



    while True:
        # 1. Line following code goes here (keep the car on the main spine)
        
        # 2. Check for branches
        if SL == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
            
        if SL == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        if drop_off_bay == target_bay:
            print("Target reached! Turning into bay")
            dropped_off = True #the package has been dropped off
            if target_bay == 0: 
                #code to go straight and drop off in red bay
                slot_status = [0,0,0,0,0,0] # Reset slot status for next checking
                break
            else:
                #code to turn 90 degrees and drop off in other bays
                # Insert code to turn 90 degrees and drop off
                slot_status = [0,0,0,0,0,0] # Reset slot status for next checking
                break # Exit loop after drop off