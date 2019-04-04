#IP 192.168.0.134
#192.168.0.67

print('Hello')


#D0=GPIO16, D1=GPIO5, D2=GPIO4, D3=GPIO0 (https://github.com/nodemcu/nodemcu-devkit-v1.0?ts=4#pin-map)
import machine
iLeft = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(5))
iMiddle = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(4))
iRight = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(0))

import vl53l0x
vLeft = vl53l0x.VL53L0X(iLeft)
vMiddle = vl53l0x.VL53L0X(iMiddle)
vRight = vl53l0x.VL53L0X(iRight)


#D5=GPIO14, D6=GPIO12
import servo
steer = servo.Servo(machine.Pin(14))
steer.write_angle(90)

motor = servo.Servo(machine.Pin(12))
motor.write_angle(90)




while True:
	vLeft.read()

def reload():
	import sys
	del sys.modules['f']
	import f
