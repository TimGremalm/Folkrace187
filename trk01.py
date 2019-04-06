import machine
import vl53l0x
import servo
import time
import sys
import math

stopped = 0
forward = 1
backward = 4
backwardleft = 5
backwardright = 6
smpowered = 0
smstart = 1
smstopped = 2

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
		
		self.distanceIgnore = 220
		self.distanceIgnoreMin = 75
		self.distanceCenter = 0
		self.distanceCenterEscalated = 0

		self.distanceAccelerate = 200
		self.accelerateSpeed = 0
		self.stopAtDistance = 70
		self.startAtDistance = 100
		
		#D7=GPIO13, D8=GPIO15
		self.startmodulePinStart = machine.Pin(13, machine.Pin.IN)
		self.aa = machine.Pin(15, machine.Pin.IN)
		self.startModuleState = smpowered

	def read(self):
		self.distanceLeft = self.vLeft.read()
		self.distanceFront = self.vFront.read()
		self.distanceRight = self.vRight.read()
		s = self.startmodulePinStart.value()
		k = self.aa.value()
		if s == 0 and k == 1:
			self.startModuleState = smpowered
		elif s == 1 and k == 1:
			self.startModuleState = smstart
		elif s == 0 and k == 0:
			self.startModuleState = smstopped

	def analyze(self):
		#Cut of distances longer then 200mm
		#79 - 250
		#
		diff = min(self.distanceRight, self.distanceIgnore) - min(self.distanceLeft, self.distanceIgnore)
		diffAbs = diff
		if diff < 0:
			diffAbs = diffAbs * -1
		self.distanceCenter = float(diffAbs) / (self.distanceIgnore - self.distanceIgnoreMin)
		self.distanceCenterEscalated = math.sqrt(self.distanceCenter)
		if diff < 0:
			self.distanceCenter = self.distanceCenter * -1
			self.distanceCenterEscalated = self.distanceCenterEscalated * -1
		#print('Center %f' % self.distanceCenter)
		print('Center Escalated %f' % self.distanceCenterEscalated)
		#self.__str()
		
		
		self.accelerateSpeed = min(self.distanceFront, self.distanceAccelerate) / self.distanceAccelerate
		#print('Distance accelerate %f %d' % (self.accelerateSpeed, self.distanceFront))

	def __str(self):
		self.read()
		print('L: %d M: %d R: %d' % (self.distanceLeft, self.distanceFront, self.distanceRight))

class motors:
	def __init__(self):
		#D5=GPIO14, D6=GPIO12
		self.servoSteering = servo.Servo(machine.Pin(14))
		self.hbridge = servo.Servo(machine.Pin(12))

		self.speedGoal = 0 #-1.0 1.0
		self.speedNow = 0 #-1.0 1.0
		self.speedRange = 15
		self.speedCenter = 90

		self.steerGoal = 0 #-1.0 1.0
		self.steerNow = 0 #-1.0 1.0
		self.steerRange = 40
		self.steerCenter = 100

	def regulate(self):
		self.servoSteering.write_angle(int(self.steerGoal * self.steerRange + self.steerCenter))
		self.hbridge.write_angle(int((self.speedGoal * self.speedRange * -1) + self.speedCenter))

	def disable(self):
		self.servoSteering.pwm.deinit()
		self.hbridge.pwm.deinit()

class trk01:
	def __init__(self):
		self.sensors = sensors()
		self.motors = motors()
		self.turns = [0]
		self.events = [(0, stopped), (0, stopped)]
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

	def eventsAdd(self, item):
		self.events.append((time.ticks_ms(), item))
		if len(self.events) > 5:
			self.events.pop(0)

	def turnsAdd(self, item):
		self.turns.append(item)
		if len(self.turns) > 20:
			self.turns.pop(0)

	def decide(self):
		state = self.events[-1][1]
		if state==stopped:
			if self.sensors.startModuleState == smstart: #Triggered by startmodule
				print('State to forward')
				self.eventsAdd(forward)
		elif state==forward:
			if self.sensors.startModuleState == smstopped:
				#Reset state and turn of motors
				self.eventsAdd(stopped)
				self.motors.speedGoal = 0
				self.motors.disable()
				return
			if self.sensors.distanceFront < self.sensors.stopAtDistance:
				#We must back out, do a avrage of previous turns to decide which turn to make
				avragePreviousTurns = sum(self.turns) / len(self.turns)
				print('Avredge previous turns: %f' % avragePreviousTurns)
				if avragePreviousTurns > 0:
					print('State to backwardleft')
					self.eventsAdd(backwardleft)
				else:
					print('State to backwardright')
					self.eventsAdd(backwardright)
		elif state==backward or state==backwardleft or state==backwardright:
			if self.sensors.startModuleState == smstopped:
				#Reset state and turn of motors
				self.eventsAdd(stopped)
				self.motors.speedGoal = 0
				self.motors.disable()
				return
			if self.sensors.distanceFront > self.sensors.startAtDistance:
				print('State to forward')
				self.eventsAdd(forward)

	def act(self):
		state = self.events[-1][1]
		if state==stopped:
			self.motors.steerGoal = 0.0
			self.motors.speedGoal = 0.0
		elif state==forward:
			self.motors.steerGoal = self.sensors.distanceCenterEscalated
			#self.motors.steerGoal = self.sensors.distanceCenter
			self.motors.speedGoal = self.sensors.accelerateSpeed
			#Add turning for statistics
			self.turnsAdd(self.motors.steerGoal)
		elif state==backward:
			self.motors.steerGoal = 0.0
			self.motors.speedGoal = -1.0
		elif state==backwardleft:
			self.motors.steerGoal = -1.0
			self.motors.speedGoal = -1.0
		elif state==backwardright:
			self.motors.steerGoal = 1.0
			self.motors.speedGoal = -1.0

	def run(self):
		run = True
		while run:
			try:
				self.sensors.read()
				self.sensors.analyze()
				self.decide()
				self.act()
				self.motors.regulate()
				#print('')
				#print(self.events)
				#print(self.turns)
				time.sleep(0.1)
			except KeyboardInterrupt:
				#Gracfully exit loop
				run = False
				pass
		#Reset state and turn of motors
		self.eventsAdd(stopped)
		self.motors.speedGoal = 0
		self.motors.disable()
		print('Exit run')
