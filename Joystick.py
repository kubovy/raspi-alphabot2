#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from Logger import Logger

class Joystick:

    NONE = 0
    CTR = 7
    A = 8
    B = 9
    C = 10
    D = 11

    state = NONE
    interrupted = False
    thread = None

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("Joystick", debug)

        GPIO.setup(self.CTR, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.A, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.B, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.C, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.D, GPIO.IN, GPIO.PUD_UP)

        self.client.publish(self.serviceName + "/state/joystick", "NONE", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/center", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/up", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/right", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/down", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/left", "OFF", 1, True)

    def looper(self):
        while (self.interrupted == False):
            try:
                if GPIO.input(self.CTR) == 0:
                    if (self.state != self.CTR):
                        self.logger.info("CENTER")
                        self.client.publish(self.serviceName + "/state/joystick", "CENTER", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/center", "ON", 1, True)
                        self.state = self.CTR
                elif GPIO.input(self.A) == 0:
                    if (self.state != self.A):
                        self.logger.info("UP")
                        self.client.publish(self.serviceName + "/state/joystick", "UP", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/up", "ON", 1, True)
                        self.state = self.A
                elif GPIO.input(self.B) == 0:
                    if (self.state != self.B):
                        self.logger.info("RIGHT")
                        self.client.publish(self.serviceName + "/state/joystick", "RIGHT", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/right", "ON", 1, True)
                        self.state = self.B
                elif GPIO.input(self.C) == 0:
                    if (self.state != self.C):
                        self.logger.info("DOWN")
                        self.client.publish(self.serviceName + "/state/joystick", "DOWN", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/down", "ON", 1, True)
                        self.state = self.C
                elif GPIO.input(self.D) == 0:
                    if (self.state != self.D):
                        self.logger.info("LEFT")
                        self.client.publish(self.serviceName + "/state/joystick", "LEFT", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/left", "ON", 1, True)
                        self.state = self.D
                else:
                    if (self.state != self.NONE):
                        self.logger.info("NONE")
                        self.client.publish(self.serviceName + "/state/joystick", "NONE", 1, True)
                        if (self.state == self.CTR): self.client.publish(self.serviceName + "/state/joystick/center", "OFF", 1, True)
                        elif (self.state == self.A): self.client.publish(self.serviceName + "/state/joystick/up", "OFF", 1, True)
                        elif (self.state == self.B): self.client.publish(self.serviceName + "/state/joystick/right", "OFF", 1, True)
                        elif (self.state == self.C): self.client.publish(self.serviceName + "/state/joystick/down", "OFF", 1, True)
                        elif (self.state == self.D): self.client.publish(self.serviceName + "/state/joystick/left", "OFF", 1, True)
                        self.state = self.NONE
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
