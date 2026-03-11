from time import sleep
from decision import delivery, events
import upperpurple_lowerorange_R_detect as detector

detector.init_laser()
from machine import Pin

S1_pin = 21
S2_pin = 20
SL_pin = 26 
SR_pin = 22

S1_sensor = Pin(S1_pin, Pin.IN)
S2_sensor = Pin(S2_pin, Pin.IN)
SL_sensor = Pin(SL_pin, Pin.IN)
SR_sensor = Pin(SR_pin, Pin.IN)
SR = SR_sensor.value()

while True:
    # pretend we just crossed a junction (update events before calling)
    # call detector using globals; pass previous laser_distance or None
    laser_distance, slot_status, slot_counter = detector.upperP_lowO_R_detect(events, laser_distance)
    # print distance sample and state for debugging
    print(f"Distance reading: {laser_distance}mm")
    print(f"Counter: {delivery['search_slot_counter']}")
    print(f"Slot status: {delivery['slot_status']}")

    sleep(2)
    # loop continues indefinitely; break manually when done


