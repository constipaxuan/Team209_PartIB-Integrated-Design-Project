from machine import PWM, ADC, Pin
ADC_SOLUTION = 65535  # Pico ADC is 16-bit (0–65535) FOR LEDs
from locations import Resistor_Color
servo = PWM(Pin(15)) #QN: is this pin correct? It shares the same pin as the 3 wire servo
servo.freq(50)
feedback = ADC(Pin(26)) #this is where the white wire goes
from time import sleep

# LED wiring
B_led = 19 # pin 19
G_led = 18 # pin 18
R_led = 17 # pin 17
Y_led = 16 # pin 16
Blue = Pin(B_led, Pin.OUT)
Green = Pin(G_led, Pin.OUT)
Red = Pin(R_led, Pin.OUT)
Yellow = Pin(Y_led, Pin.OUT)
#Initialize Blue Red Green Yellow color to off
Blue.value(0)
Green.value(0)
Red.value(0)
Yellow.value(0)
# Sensor connected to ADC0 (GP26)
sensor = ADC(28)

servo_claw = PWM(Pin(13))
servo_claw.freq(50) # Standard 50Hz frequency
servo_tilt = PWM(Pin(15)) #QN: is this pin correct? It shares the same pin as the 3 wire servo
servo_tilt.freq(50)

def claw(angle):
    # Map 0-270 degrees to 500-2500 microseconds
    # Pico PWM duty is 0-65535. 
    # 50Hz period is 20ms. 500us = 2.5% duty. 2500us = 12.5% duty.
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_claw.duty_u16(duty)

def turn_claw(angle):
    pulse_width = 500 + (angle / 270) * 2000
    duty = int((pulse_width / 20000) * 65535)
    servo_tilt.duty_u16(duty)

def R_measure():
    #pass current through and measure voltage V&I
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION
    sleep(0.1) # delay to stabilize reading
    voltage = 3.3*sensor.read_u16()/ADC_SOLUTION 
    #this is the final voltage reading

    if voltage > 3:
        Blue.value(1) #turns LED on to blue
        resistor_color = Resistor_Color.blue # Blue
    elif 2.5 < voltage <= 3:
        Green.value(1)
        resistor_color = Resistor_Color.green # Green
    elif 1 < voltage <= 2.5:
        Red.value(1)
        resistor_color = Resistor_Color.red # Red
    elif 0.2 < voltage <= 1:
        Yellow.value(1)
        resistor_color = Resistor_Color.yellow # Yellow
    return resistor_color

def test():
    claw(10)
    sleep(0.5)
    turn_claw(10)
    sleep(0.5)
    resistor_color = R_measure()
    print(f"Color: {resistor_color}")


test()
