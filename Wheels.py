#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from AlphaBot import AlphaBot
from Logger import Logger

class Wheels:

    DEFAULT_TIMEOUT = 500
    timeout=-1 

    interrupted = False
    thread = None

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("Wheels", debug)
        self.alphabot = AlphaBot()
        
        self.halt()        
        self.client.message_callback_add(self.serviceName + "/control/move/#", self.on_message)
        self.client.message_callback_add(self.serviceName + "/control/rotate/#", self.on_message)
        self.client.message_callback_add(self.serviceName + "/control/turn/#", self.on_message)
        self.client.message_callback_add(self.serviceName + "/control/stop/#", self.on_message)
       
    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if (len(path) > 1 and path[0] == self.serviceName and path[1] == "control"): # mutinus/control/#
                if (len(path) > 2 and path[2] == "move"):                                # mutinus/control/move/#
                    if (len(path) > 3 and path[3] == "forward"):                         # mutinus/control/move/forward
                        parts = msg.payload.split(" ")
                        if (len(parts) > 0):
                            speed = float(parts[0])
                            timeout = int(parts[1]) if len(parts) > 1 else self.DEFAULT_TIMEOUT
                            self.move(speed, speed, timeout)
                    elif (len(path) > 3 and path[3] == "backward"):                      # mutinus/control/move/backward
                        parts = msg.payload.split(" ")
                        if (len(parts) > 0):
                            speed = float(parts[0])
                            timeout = int(parts[1]) if len(parts) > 1 else self.DEFAULT_TIMEOUT
                            self.move(-speed, -speed, timeout)
                    else:                                                                 # mutinus/control/move
                        parts = msg.payload.split(" ")
                        if (len(parts) > 0):
                            left = float(parts[0])
                            right =  float(parts[1]) if len(parts) > 1 else left
                            timeout = int(parts[2]) if len(parts) > 2 else self.DEFAULT_TIMEOUT
                            self.move(left, right, timeout)
                elif (len(path) > 2 and path[2] == "rotate"):                             # mutinus/control/rotate
                    parts = msg.payload.split(" ")
                    if (len(parts) > 0):
                        speed = float(parts[0])
                        timeout = int(parts[1]) if len(parts) > 1 else self.DEFAULT_TIMEOUT
                        if (len(path) > 3 and path[3] == "right"):                        # mutinus/control/rotate/right
                            self.move(speed, 0, timeout)
                        elif (len(path) > 3 and path[3] == "left"):                       # mutinus/control/rotate/left
                            self.move(0, speed, timeout)
                elif (len(path) > 2 and path[2] == "turn"):                               # mutinus/control/turn
                    parts = msg.payload.split(" ")
                    if (len(parts) > 0):
                        speed = float(parts[0])
                        timeout = int(parts[1]) if len(parts) > 1 else self.DEFAULT_TIMEOUT
                        if (len(path) > 3 and path[3] == "right"):                        # mutinus/control/turn/right
                            self.move(speed, -speed, timeout)
                        elif (len(path) > 3 and path[3] == "left"):                       # mutinus/control/turn/left
                            self.move(-speed, speed, timeout)
                elif (len(path) > 2 and path[2] == "stop"):                               # mutinus/control/stop
                    self.halt()
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def move(self, left, right, timeout = DEFAULT_TIMEOUT):
        self.timeout = time.time() * 1000 + timeout
        if (left < -100): left = -100
        if (left > 100): left = 100
        if (right < -100): left = -100
        if (right > 100): left = 100
        self.client.publish(self.serviceName + "/state/move/left", str(left), 1, True)
        self.client.publish(self.serviceName + "/state/move/right", str(right), 1, True)
        self.client.publish(self.serviceName + "/state/move", str(left) + " " + str(right), 1, True)
        self.logger.info("Moving left at " + str(left) + "%, right at " + str(right) + "%")
        self.alphabot.setMotor(left, right)

    def halt(self):
        self.client.publish(self.serviceName + "/state/move/left", "0", 1, True)
        self.client.publish(self.serviceName + "/state/move/right", "0", 1, True)
        self.client.publish(self.serviceName + "/state/move", "0 0", 1, True)
        self.logger.info("Stop moving")
        self.alphabot.stop()

    def looper(self):
        while (self.interrupted == False):
            try:
                if (self.timeout > 0): self.logger.debug("Timeout in: " + str(self.timeout - time.time() * 1000) + "ms")
                if (self.timeout > 0 and self.timeout < time.time() * 1000):
                    self.timeout = -1
                    self.halt()
                time.sleep(0.1)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
        self.halt()
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
 
