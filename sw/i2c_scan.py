from machine import Pin, I2C
from time import sleep_ms

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
sleep_ms(100)
print(i2c.scan())