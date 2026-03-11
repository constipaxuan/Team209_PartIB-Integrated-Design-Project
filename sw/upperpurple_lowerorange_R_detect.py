#define these variables globally so that we can clear them off and reuse them for other branches
from behaviour import Mode, Delivery_States, Delivery_Rack_States
from locations import Resistor_Color, Junctions, Direction
from map_state import memory
from machine import Pin, I2C
from locations import Junctions
from libs.VL53L0X.VL53L0X import VL53L0X

#for test purposes only
S1_pin = 21
S2_pin = 20
SL_pin = 26
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)
SR = SR_sensor.value()

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
    i2c_bus = I2C(id=1, sda=Pin(10), scl=Pin(11)) # I2C0 on GP8 & GP9
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
    laser_distance = vl53l0.read()
    # Stop device
    vl53l0.stop()
    return laser_distance

# --- WILL BE DEFINED IN MAIN LOOP TO ENABLE THE USE OF JUNCTION TYPE DIRECTLY ---
on_junction = (SR == 1)
events["new_junction"] = (not memory["prev_on_junction"] and on_junction)

if events["new_junction"]:
    events["junction_type"] = detect_junction_type(SR)
else:
    events["junction_type"] = Junctions.nil
# --- END ---

# --- WILL BE DEFINED IN MAIN LOOP TO ENABLE THE USE OF JUNCTION TYPE DIRECTLY ---
on_junction = (SR == 1)
events["new_junction"] = (not memory["prev_on_junction"] and on_junction)

if events["new_junction"]:
    events["junction_type"] = detect_junction_type(SR)
else:
    events["junction_type"] = Junctions.nil
# --- END ---

def upperP_lowO_R_detect(events, laser_distance, delivery, robot):
    
    # ONLY act if this is a BRAND NEW junction detection
    if events["new_junction"] == True and not events["new_T"]:
        # 1. Safety check: stop the counter if we run out of slots (All slots have been cleared for a particular rack)
        if delivery["search_slot_counter"] >= 6: # 6 slots
            if robot["target_rack_idx"] < 3:
                robot["target_rack_idx"] += 1
            else:
                robot["target_rack_idx"] = 0
            delivery["search_slot_counter"] = 0
            delivery["slot_status"] = [0,0,0,0,0,0]
            return

        else:
            motor_l.Forward(speed = 0)
            motor_r.Forward(speed = 0)
            # 2. Fire the laser ONCE
            laser_distance = rec_dist_laser() 

            # 3. Update the CURRENT slot
            if laser_distance < 100: 
                delivery["R_detected"] = True
                delivery["delivery_state"] = Delivery_States.pickup
                delivery["ready_for_unloading"] = False
                delivery["rack_state"] = Delivery_Rack_States.load_detected
                delivery["search_slot_counter"] += 1
            else:
                delivery["slot_status"][delivery["search_slot_counter"]] = 1
                delivery["search_slot_counter"] += 1
                #mark the slot as cleared
            return laser_distance


        """
    global R_detected, rack_cleared, slot_counter, slot_status
    
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
        slot_counter += 1 """