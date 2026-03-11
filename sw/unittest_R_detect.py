from time import sleep
import upperpurple_lowerorange_R_detect as detector

detector.init_laser()

while True:
    # pretend we just crossed a junction
    distance = detector.upperP_lowO_R_detect(new_junction=True, prev_on_junction=False)
    # print distance sample and state for debugging
    print(f"Distance reading: {distance}mm")
    print(f"Counter: {detector.slot_counter}")
    print(f"Slot status: {detector.slot_status}")

    sleep(2)
    # loop continues indefinitely; break manually when done


