
from locations import Junctions

slot_status = [0,0,0,0,0,0] #0 means unknown slot status, 1 means cleared
slot_counter = 0
#set up laser sensor

from machine import Pin, I2C
from libs.VL53L0X.VL53L0X import VL53L0X

#will delete later, for test purposes below
S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)

def detect_junction_type(SL, SR):
    if (SL == 1 and SR == 0): 
        return Junctions.L
    elif (SL == 0 and SR == 1):
        return Junctions.R
    elif (SL == 1 and SR == 1):
        return Junctions.RL
    return Junctions.nil

def init_laser():
    # config I2C Bus
    i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
    # print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
        
    # Setup vl53l0 object
    global vl53l0
    vl53l0 = VL53L0X(i2c_bus)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
    vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

def rec_dist_laser():
    # Start device
    vl53l0.start()
    # Read one sample
    distance = vl53l0.read()
    # Stop device
    vl53l0.stop()
    return distance
    

def upperP_lowO_R_detect(new_junction, prev_on_junction):
    global R_detected, slot_counter, slot_status
    
    
    # ONLY act if this is a BRAND NEW junction detection AND it's a right or right-left junction
    if new_junction and not prev_on_junction:
        # 2. Fire the laser ONCE
        distance = rec_dist_laser()
        
        # 3. Update the CURRENT slot
        if distance < 300: 
            R_detected = True
            print(f"Slot {slot_counter} has a resistor.")
        # then run code to pick up resistor here
        else:
            slot_status[slot_counter] = 1
            print(f"Slot {slot_counter} is empty.")

        # 4. NOW move the counter to the next slot for the NEXT branch
        slot_counter += 1
        return distance
    
    #test this out, might change (remember the current sensor state for the next call)
    #prev_on_junction = new_junction (Uncomment this if the first test works)