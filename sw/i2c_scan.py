from machine import Pin, I2C
from time import sleep_ms
from libs.VL53L0X.VL53L0X import VL53L0X

print("testing right laser)")
i2c_bus = I2C(id=1, sda=Pin(10), scl=Pin(11), freq=100000) # I2C1 on GP10 & GP11
vl53l0_R = VL53L0X(i2c_bus)
vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[0], 18)
vl53l0_R.set_Vcsel_pulse_period(vl53l0_R.vcsel_period_type[1], 14)
print("right scan:", vl53l0_R.scan())

print("testing left laser)")
i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
vl53l0_L = VL53L0X(i2c_bus)
vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[0], 18)
vl53l0_L.set_Vcsel_pulse_period(vl53l0_L.vcsel_period_type[1], 14)
print("right scan:", vl53l0_L.scan())
