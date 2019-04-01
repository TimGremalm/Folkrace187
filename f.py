#IP 192.168.0.134

print('Hello')

import machine
#D0 = GPIO16, D1 = GPIO5 (https://github.com/nodemcu/nodemcu-devkit-v1.0?ts=4#pin-map)
i = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(5))

import vl53l0x
v = vl53l0x.VL53L0X(i)
v.read()

def reload():
	import sys
	del sys.modules['f']
	import f
