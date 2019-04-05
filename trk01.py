import machine
import vl53l0x
import servo
import time
import sys

class sensors:
	def __init__(self):
		#D0=GPIO16, D1=GPIO5, D2=GPIO4, D3=GPIO0 (https://github.com/nodemcu/nodemcu-devkit-v1.0?ts=4#pin-map)
		self.iLeft = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(5))
		self.iFront = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(4))
		self.iRight = machine.I2C(scl=machine.Pin(16), sda=machine.Pin(0))

		self.vLeft = vl53l0x.VL53L0X(self.iLeft)
		self.vFront = vl53l0x.VL53L0X(self.iFront)
		self.vRight = vl53l0x.VL53L0X(self.iRight)
		
		self.distanceLeft = 0
		self.distanceFront = 0
		self.distanceRight = 0
		
		self.distanceIgnore = 200
		self.distanceCenter = 0

	def read(self):
		self.distanceLeft = self.vLeft.read()
		self.distanceFront = self.vFront.read()
		self.distanceRight = self.vRight.read()

	def analyze(self):
		diff = abs()
		self.distanceCenter = min

	def __str(self):
		self.read()
		print('L: %d M: %d R: %d' % (self.distanceLeft, self.distanceFront, self.distanceRight))

class motors:
	def __init__(self):
		#D5=GPIO14, D6=GPIO12
		self.servoSteering = servo.Servo(machine.Pin(14))
		self.servoSteering.write_angle(110)
		self.hbridge = servo.Servo(machine.Pin(12))
		self.hbridge.write_angle(90)

		self.speedGoal = 0 #-1.0 1.0
		self.speedNow = 0 #-1.0 1.0
		self.speedRange = 15
		self.speedCenter = 90

		self.steerGoal = 0 #-1.0 1.0
		self.steerNow = 0 #-1.0 1.0
		self.steerRange = 30
		self.steerCenter = 90

	def regulate(self):
		diff = self.steerGoal - self.steerNow
		if diff > 0:
			self.steerNow += 0.1
			if self.steerNow > self.steerGoal:
				self.steerNow = self.steerGoal
		elif diff < 0:
			self.steerNow -= 0.1
			if self.steerNow < self.steerGoal:
				self.steerNow = self.steerGoal
		if diff != 0:
			self.servoSteering.write_angle(int(self.steerNow * self.steerRange + self.steerCenter))

		diff = (self.speedGoal * -1) - self.speedNow
		if diff > 0:
			self.speedNow += 0.1
			if self.speedNow > self.speedGoal:
				self.speedNow = self.speedGoal
		elif diff < 0:
			self.speedNow -= 0.1
			if self.speedNow < self.speedGoal:
				self.speedNow = self.speedGoal
		if diff != 0:
			self.hbridge.write_angle(int(self.speedNow * self.speedRange + self.speedCenter))

	def disable(self):
		self.servoSteering.pwm.deinit()
		self.hbridge.pwm.deinit()

class trk01:
	def __init__(self):
		self.sensors = sensors()
		self.motors = motors()
		print('TRK-01 loaded')

	def reload(self):
		import sys
		self.motors.disable()
		self.motors = None
		self.sensors.vLeft.stop()
		self.sensors.vFront.stop()
		self.sensors.vRight.stop()
		self.sensors.iLeft.stop()
		self.sensors.iFront.stop()
		self.sensors.iRight.stop()
		self.sensors = None
		del sys.modules['trk01']
		#del trk01
		#del t

	def run(self):
		run = True
		while run:
			try:
				d = time.ticks_ms()
				self.sensors.read()
				self.sensors.analyze()
				self.motors.regulate()
				time.sleep(0.1)
			except KeyboardInterrupt:
				run = False
				self.motors.speedGoal = 0
				pass
