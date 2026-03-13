from machine import Pin, I2C
from time import sleep_ms
from libs.VL53L0X.VL53L0X import VL53L0X

i2c = I2C(1, scl=Pin(11), sda=Pin(10), freq=100000)
sleep_ms(100)

print("scan:", i2c.scan())

