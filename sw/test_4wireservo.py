from machine import Pin, PWM, ADC
import time

# Setup Control (GP15) and Feedback (GP26)
servo = PWM(Pin(15))
servo.freq(50)
feedback = ADC(Pin(26)) #this is where the white wire goes

def get_actual_angle():
    # Read raw 16-bit value (0-65535)
    raw_value = feedback.read_u16()
    # Convert to voltage (0-3.3V)
    voltage = (raw_value / 65535) * 3.3
    
    # y = 3.1817x + 78.69
    # Where y is the feedback value and x is the angle.
    # We solve for x: x = (y - 78.69) / 3.1817
    adc_10bit = (raw_value / 65535) * 1023
    calculated_angle = (adc_10bit - 78.69) / 3.1817
    return max(0, min(270, calculated_angle))

def move_and_check(target_angle):
    pulse_width = 500 + (target_angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo.duty_u16(duty)
    
    time.sleep(0.5) # Give it time to move
    actual = get_actual_angle()
    print(f"Target: {target_angle} | Actual: {actual:.2f} degrees")

# Run Test
while True:
    move_and_check(0)
    time.sleep(1)
    move_and_check(135)
    time.sleep(1)
    move_and_check(270)
    time.sleep(1)