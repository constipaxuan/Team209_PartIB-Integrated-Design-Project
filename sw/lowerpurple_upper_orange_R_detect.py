
from RHS_dropoff import RHS_dropoff
from sw.behaviour import Mode
from sw.locations import Resistor_Color
from sw.map_state import SL
#define these variables globally so that we can clear them off and reuse them for other branches
global slot_status
slot_status = [0,0,0,0,0,0] #0 means unknown slot status, 1 means cleared
slot_counter = 0
resistor_color = Resistor_Color.none
cleared_counter = slot_status.count(1)
rack_cleared = False
R_detected = False
#set up laser sensor
motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 
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
    

def lowP_upperO_R_detect(new_junction):
    global R_detected, rack_cleared, slot_counter, slot_status
    # ONLY act if this is a BRAND NEW junction detection
    if new_junction and SL == 1:
        # 1. Safety check: stop the counter if we run out of slots
        if slot_counter >= len(slot_status):
            print("All slots checked. Stopping counter.")
            return

        # 2. Fire the laser ONCE
        distance = rec_dist_laser() 
        
        # 3. Update the CURRENT slot
        if distance < 100: 
            R_detected = True
            print(f"Slot {slot_counter} has a resistor.")
        # then run code to pick up resistor here
        else:
            slot_status[slot_counter] = 1
            print(f"Slot {slot_counter} is empty.")

        # 4. NOW move the counter to the next slot for the NEXT branch
        slot_counter += 1



