# Coming from the LHS main spine back down to loading bays
# Red = 0, Yellow = 1, SKIP the starting box = 2, Green = 3, Blue = 4
target_bay = 0 
drop_off_bay = 0
counting_line = False # This is our "latch"

def LHS_dropoff(resistor_color):
    if resistor_color == 0: 
        target_bay = 4 # Red, which is the rightmost bay
    if resistor_color == 1: 
        target_bay = 3 # Yellow
    if resistor_color == 3: 
        target_bay = 1 # Green, skip 1 to skip the starting box
    if resistor_color == 4: 
        target_bay = 0 # Blue



    while True:
        # 1. Line following code goes here (keep the car on the main spine)
        
        # 2. Check for branches
        if SR == 1 and not counting_line:
            drop_off_bay += 1
            counting_line = True # Block further counting until we leave the line
            print(f"Passing branch {drop_off_bay}")
            
        if SR == 0:
            counting_line = False # Reset the latch once we are back on black
            
        # 3. Check if we reached our target
        if drop_off_bay == target_bay:
            print("Target reached! Turning into bay")
            if target_bay == 0: 
                #code to go straight and drop off in blue bay
                slot_status = [0,0,0,0,0,0] # Reset slot status for next checking
                break
            else:
                #code to turn 90 degrees and drop off in other bays
                # Insert code to turn 90 degrees and drop off
                slot_status = [0,0,0,0,0,0] # Reset slot status for next checking
                break # Exit loop after drop off