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
    
# Result: Button works as expected. Reads 0 when not pressed, 1 when pressed. ON toggles between True and False with each press. Debouncing works, as long as button is not pressed again within 200ms of the last press.
# But print is causing delayed response. Will remove print statements in final code.