from upperpurple_lowerorange_R_detect import upperP_lowO_R_detect, slot_counter, slot_status, rec_dist_laser
#from line_following import detect_junction
from time import sleep

new_junction = True
while True:
    # Simulate detecting a new junction (for testing purposes)
    # In real implementation, this would be based on sensor input
    upperP_lowO_R_detect(new_junction)
    print(f"Distance reading: {rec_dist_laser()}mm")  # Print distance reading for debugging
    sleep(2)
    print(f"Counter: {slot_counter}")
    print(f"list: {slot_status}")

