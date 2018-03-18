#!/usr/bin/python
# -*- coding:utf-8 -*-
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

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
        self.logger = Logger("CameraServo", debug)
        
        self.pwm = PCA9685(0x40, debug)
        self.pwm.setPWMFreq(50)
    
        self.client.message_callback_add(self.serviceName + "/control/camera/#", self.on_message)
        
        self.set_position(0, self.ROLL_MID, self.ROLL_MIN, self.ROLL_MAX)
        self.set_position(1, self.PITCH_MID, self.PITCH_MIN, self.PITCH_MAX)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "camera":                               # mutinus/control/camera/#
                    degrees = -float(msg.payload)
                    if len(path) > 3 and (path[3] == "roll" or path[3] == "0"):         # mutinus/control/camera/0/#
                        if len(path) > 4 and path[4] == "deg":                          # mutinus/control/camera/0/deg
                            self.set_position_degrees(0, degrees, self.ROLL_MID, self.ROLL_MIN, self.ROLL_MAX,
                                                      self.ROLL_DEG)
                        elif len(path) > 4 and path[4] == "percent":
                            self.set_position_percent(0, int(msg.payload), self.ROLL_MIN, self.ROLL_MAX)
                        else:                                                           # mutinus/control/camera/roll
                            self.set_position(0, int(msg.payload), self.ROLL_MIN, self.ROLL_MAX)
                    if len(path) > 3 and (path[3] == "pitch" or path[3] == "1"):        # mutinus/control/camera/0/#
                        if len(path) > 4 and path[4] == "deg":                          # mutinus/control/camera/0/deg
                            self.set_position_degrees(1, degrees, self.PITCH_MID, self.PITCH_MIN, self.PITCH_MAX,
                                                      self.PITCH_DEG)
                        elif len(path) > 4 and path[4] == "percent":
                            self.set_position_percent(1, int(msg.payload), self.PITCH_MIN, self.PITCH_MAX)
                        else:                                                           # mutinus/control/camera/pitch
                            self.set_position(1, int(msg.payload), self.PITCH_MIN, self.PITCH_MAX)
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def roll_percent(self, percent):
        self.set_position_percent(0, percent, self.ROLL_MIN, self.ROLL_MAX)

    def pitch_percent(self, percent):
        self.set_position_percent(1, percent, self.PITCH_MIN, self.PITCH_MAX)

    def set_position(self, servo, position, position_min, position_max):
        original = position
        if position > position_max: position = position_max
        if position < position_min: position = position_min
        self.logger.debug(str(original) + " -> " + str(position))

        self.client.publish(self.serviceName + "/state/camera/" + str(servo) + "/raw", position, 0, True)

        percent = 100 - int(float(position - position_min) * 100.0 / float(position_max - position_min))
        self.client.publish(self.serviceName + "/state/camera/" + str(servo) + "/percent", percent, 1, True)
        
        self.pwm.setServoPulse(servo, position)
        threading.Timer(0.5, self.stop).start()

    def set_position_percent(self, servo, percent, position_min, position_max):
        if percent > 100: percent = 100
        if percent < 0: percent = 0
        position = position_min + int((100.0 - float(percent)) * float(position_max - position_min) / 100.0)
        self.logger.debug(str(percent) + "% -> " + str(position))
        self.set_position(servo, position, position_min, position_max)

    def set_position_degrees(self, servo, degrees, mid, position_min, position_max, points_per_degree):
        position = int(degrees * points_per_degree + mid)
        self.logger.debug(str(degrees) + "deg -> " + str(position))
        self.set_position(servo, position, position_min, position_max)

    def stop(self):
        self.logger.debug("Stopping")
        self.pwm.stop(0)
        self.pwm.stop(1)
