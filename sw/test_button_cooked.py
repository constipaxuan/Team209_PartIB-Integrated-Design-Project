from machine import Pin, PWM
from time import sleep, ticks_ms, ticks_diff

button = Pin(14, Pin.IN)

prev_button = 0
ON = False
last_press = 0

while True:
    button_now = button.value()

    # non blocking debouncing. this allows sensors to still be read while button is being debounced, preventing missed junctions.
    if button_now == 1 and prev_button == 0:
        if ticks_diff(ticks_ms(), last_press) > 200:
            ON = not ON
            last_press = ticks_ms()
    
    prev_button = button_now 

    print(button_now, ON, prev_button)
    