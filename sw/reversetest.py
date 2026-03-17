from machine import Pin, PWM, I2C, ADC
from time import sleep

class Motor:
    def __init__(self, dirPin, PWMPin):
        self.mDir = Pin(dirPin, Pin.OUT)  # set motor direction pin
        self.pwm = PWM(Pin(PWMPin))  # set motor pwm pin
        self.pwm.freq(1000)  # set PWM frequency
        self.pwm.duty_u16(0)  # set duty cycle - 0=off
        
    def off(self):
        self.pwm.duty_u16(0)
        
    def Forward(self, speed=100):
        self.mDir.value(0)                     # forward = 0 reverse = 1 motor
        self.pwm.duty_u16(int(65535 * speed / 100))  # speed range 0-100 motor

    def Reverse(self, speed=100):
        self.mDir.value(1)
        self.pwm.duty_u16(int(65535 * speed / 100))

motor_l = Motor(dirPin=4, PWMPin=5)
motor_r = Motor(dirPin=7, PWMPin=6) 

motor_l.Forward(speed=40)
motor_r.Forward(speed=40)
sleep(2)

motor_l.Forward(speed=0)
motor_r.Forward(speed=0)
sleep(1)

motor_l.Reverse(speed=40)
motor_r.Reverse(speed=40)
sleep(2)

motor_l.Forward(speed=0)
motor_r.Forward(speed=0)