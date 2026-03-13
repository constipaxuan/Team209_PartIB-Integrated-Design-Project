from machine import Pin, I2C
from time import sleep_ms
from VL53L0X import VL53L0X

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
sleep_ms(100)

print("scan:", i2c.scan())

tof = VL53L0X(i2c)
print("constructed")

tof.start()
print("started")

while True:
    print(tof.read())
    sleep_ms(100)