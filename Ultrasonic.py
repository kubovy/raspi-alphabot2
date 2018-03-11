#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from Logger import Logger

class Ultrasonic:

    TRIG = 22
    ECHO = 27

    delay=0
    last=-1

    interrupted = False
    thread = None

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("Ultrasonic", debug)
        
        GPIO.setup(self.TRIG, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ECHO, GPIO.IN)
        
        self.client.message_callback_add(self.serviceName + "/control/distance/#", self.on_message)
        
    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if (len(path) > 1 and path[0] == self.serviceName and path[1] == "control"): # mutinus/control/#
                if (len(path) > 2 and path[2] == "distance"):                            # mutinus/control/distance
                    if (msg.payload == "" or msg.payload == "MEASURE"):
                        distance = self.getDistance()
                        self.logger.info("Measuring distance: " + str(distance))
                        self.client.publish(self.serviceName + "/state/distance", distance, 1, False)
                    else:
                        self.delay = 0 if (msg.payload == "OFF") else int(float(msg.payload))
                        if (self.delay <= 0): self.delay = 0 
                        self.client.publish(self.serviceName + "/state/distance/delay", str(self.delay), 1, False)
                        self.last = -1 if (self.delay <= 0) else time.time() * 1000.0
                        self.logger.info("Measuring distance each " + str(self.delay) + "ms")
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def getDistance(self):
        GPIO.output(self.TRIG, GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(self.TRIG, GPIO.LOW)
        while not GPIO.input(self.ECHO):
            pass
        t1 = time.time()
        while GPIO.input(self.ECHO):
            pass
        t2 = time.time()
        return (t2 - t1) * 340000 / 2

    def looper(self):
        while (self.interrupted == False):
            try:
                if (self.delay > 0 and self.last > 0 and time.time() * 1000.0 - self.last > self.delay):
                    distance = self.getDistance()
                    self.logger.info("Distance: " + str(distance) + "mm")
                    self.client.publish(self.serviceName + "/state/distance", str(distance), 1, False)
                    self.last = time.time() * 1000.0
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
