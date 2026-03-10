from upperpurple_lowerorange_R_detect import upperP_lowO_R_detect, slot_counter, slot_status
from time import sleep
new_junction = True
while True:
    # Simulate detecting a new junction (for testing purposes)
    # In real implementation, this would be based on sensor input
    upperP_lowO_R_detect(new_junction)
    sleep(2)
    print(f"Counter: {slot_counter}")
    print(f"list: {slot_status}")

