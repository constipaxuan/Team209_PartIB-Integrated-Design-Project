from RHS_dropoff import RHS_dropoff
#define these variables globally so that we can clear them off and reuse them for other branches
slot_status = [0,0,0,0,0,0] #0 means unknown slot status, 1 means cleared
resistor_color = 0 
slot_counter = 0
cleared_counter = slot_status.count(1)
rack_cleared = False
#set up laser sensor
from email.mime import base
from turtle import distance

from machine import Pin, I2C
from libs.VL53L0X.VL53L0X import VL53L0X
from utime import sleep


# config I2C Bus
i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
# print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
    
# Setup vl53l0 object
vl53l0 = VL53L0X(i2c_bus)
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

def rec_dist_laser():
     # Start device
    vl53l0.start()

    laser_distance = vl53l0.read()
    print(f"Distance = {laser_distance}mm")  # Check calibration!
        
    # Stop device
    vl53l0.stop()

    return laser_distance
    

def lowP_upperO_R_detect():
    while slot_status.count(1) < 6: #number of cleared slots is less than 6
        if SL == 1:  # Branch detected

            sleep(0.1) # Short delay to debounce the sensor
            distance = rec_dist_laser()
        
            if distance < 100: # resistor detected
            # 1. Add code here to turn the car and pick up resistor
                motor_l.Reverse(speed = 50)
                motor_r.Forward(speed = 50)
                sleep(1) # might need to adjust time depending on how long it takes to turn 90 degrees. Might also want to add some sort of feedback system to determine when to stop turning instead of just relying on time.
                motor_l.Forward(speed = base)
                motor_r.Forward(speed = base)
                sleep (1) #car move forward and closer to resistor
                motor_l.Forward(speed = 0)
                motor_r.Forward(speed = 0)
              # 2. Once picked up resistor, mark as cleared
                slot_status[slot_counter] = 1
                #add code to measure resistor color and store resistor color as a variable
                motor_l.Reverse(speed = 50)
                motor_r.Reverse(speed = 50) #After grabbing R, the car reverses
                sleep(1) # might need to adjust time depending on how long it takes to reverse. Might also want to add some sort of feedback system to determine when to stop reversing instead of just relying on time.
                motor_l.Forward(speed = 50)
                motor_r.Reverse(speed = 50) #turns 90 degrees to face the dropoff bay
                #add code for it to travel to dropoff bay
                # add code to return the resistor and clear out the list
                RHS_dropoff() # Call RHS dropoff to drop off resistor from RH bay
                print(f"Slot {slot_counter} picked up and cleared.")
            else: # Slot is empty
                slot_status[slot_counter] = 1
                print(f"Slot {slot_counter} was already empty. Marked cleared.")
        
            slot_counter += 1 # Move to next slot index for the next branch
        
            #while below so it doesn't count the same branch multiple times.
            while SL == 1:
                pass 
    rack_cleared = True



