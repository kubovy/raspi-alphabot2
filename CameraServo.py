#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import threading
import traceback
import paho.mqtt.client as mqtt
from PCA9685 import PCA9685
from Logger import Logger

class CameraServo:
 
    ROLL_MIN = 750
    ROLL_MID = 1750
    ROLL_MAX = 2750
    ROLL_DEG = float(ROLL_MAX - ROLL_MIN) / 180.0
    PITCH_MIN = 1150
    PITCH_MID = 2100
    PITCH_MAX = 2800
    PITCH_DEG = ROLL_DEG

    delay = 0
    interrupted = False
    thread = None

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("CameraServo", debug)
        
        self.pwm = PCA9685(0x40, debug)
        self.pwm.setPWMFreq(50)
    
        self.client.message_callback_add(self.serviceName + "/control/camera/#", self.on_message)
        
        self.setPosition(0, self.ROLL_MID, self.ROLL_MIN, self.ROLL_MAX)
        self.setPosition(1, self.PITCH_MID, self.PITCH_MIN, self.PITCH_MAX)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if (len(path) > 1 and path[0] == self.serviceName and path[1] == "control"): # mutinus/control/#
                if (len(path) > 2 and path[2] == "camera"):                              # mutinus/control/camera/#
                    degrees = -float(msg.payload)
                    if (len(path) > 3 and (path[3] == "roll" or path[3] == "0")):        # mutinus/control/camera/roll/#
                        if (len(path) > 4 and path[4] == "raw"):                         # mutinus/control/camera/roll/raw
                            self.setPosition(0, int(msg.payload), self.ROLL_MIN, self.ROLL_MAX)
                        elif (len(path) > 4 and path[4] == "percent"):
                            self.setPositionPercent(0, int(msg.payload), self.ROLL_MIN, self.ROLL_MAX)
                        else:                                                            # mutinus/control/camera/roll
                            self.setPositionDegrees(0, degrees, self.ROLL_MID, self.ROLL_MIN, self.ROLL_MAX, self.ROLL_DEG)
                    if (len(path) > 3 and (path[3] == "pitch" or path[3] == "1")):       # mutinus/control/camera/pitch/#
                        if (len(path) > 4 and path[4] == "raw"):                         # mutinus/control/camera/pitch/raw
                            self.setPosition(1, int(msg.payload), self.PITCH_MIN, self.PITCH_MAX)
                        elif (len(path) > 4 and path[4] == "percent"):
                            self.setPositionPercent(1, int(msg.payload), self.PITCH_MIN, self.PITCH_MAX)
                        else:                                                            # mutinus/control/camera/pitch
                            self.setPositionDegrees(1, degrees, self.PITCH_MID, self.PITCH_MIN, self.PITCH_MAX, self.PITCH_DEG)
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()
            
    def setPosition(self, servo, position, min, max):
        self.delay = 0
        original = position
        if (position > max): position = max
        if (position < min): position = min
        self.logger.debug(str(original) + " -> " + str(position))

        self.client.publish(self.serviceName + "/state/camera/" + str(servo) + "/raw", position, 0, True)

        percent = 100 - int(float(position - min) * 100.0 / float(max - min))
        self.client.publish(self.serviceName + "/state/camera/" + str(servo) + "/percent", percent, 1, True)
        
        self.pwm.setServoPulse(servo, position)
        self.delay = time.time() * 1000.0 + 500.0

    def setPositionPercent(self, servo, percent, min, max):
        position = min + int((100.0 - float(percent)) * float(max - min) / 100.0)
        self.logger.debug(str(percent) + "% -> " + str(position))
        self.setPosition(servo, position, min, max)

    def setPositionDegrees(self, servo, degrees, mid, min, max, pointsPerDegree):
        position = int(degrees * pointsPerDegree + mid)
        self.logger.debug(str(degrees) + "deg -> " + str(position))
        self.setPosition(servo, position, min, max)
        
    def looper(self):
        while (self.interrupted == False):
            try:
                if (self.delay > 0 and self.delay < time.time() * 1000.0):
                    self.logger.debug("Stopping")
                    self.delay = 0
                    self.pwm.stop(0)
                    self.pwm.stop(1)
                time.sleep(0.1)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
        self.logger.info("Exiting looper")

    def start(self):
        self.interrupted = False
        self.thread = threading.Thread(target = self.looper)
        self.thread.start()
        return self.thread
    
    def stop(self):
        self.interrupted = True
        if (self.thread != None): self.thread.join(5)
        self.thread = None
