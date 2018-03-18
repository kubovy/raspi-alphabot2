#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from AlphaBot import AlphaBot
from Logger import Logger


class Wheels:

    DEFAULT_TIMEOUT = 0.5

    interrupted = False
    thread = None
    timer = None

    left = 0
    right = 0

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
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
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "move":                                 # mutinus/control/move/#
                    if len(path) > 3 and path[3] == "forward":                          # mutinus/control/move/forward
                        parts = msg.payload.split(" ")
                        if len(parts) > 0:
                            speed = float(parts[0])
                            timeout = float(parts[1]) / 1000.0 if len(parts) > 1 else self.DEFAULT_TIMEOUT
                            self.move(speed, speed, timeout)
                    elif len(path) > 3 and path[3] == "backward":                       # mutinus/control/move/backward
                        parts = msg.payload.split(" ")
                        if len(parts) > 0:
                            speed = float(parts[0])
                            timeout = float(parts[1]) / 1000.0 if len(parts) > 1 else self.DEFAULT_TIMEOUT
                            self.move(-speed, -speed, timeout)
                    else:                                                               # mutinus/control/move
                        parts = msg.payload.split(" ")
                        if len(parts) > 0:
                            left = float(parts[0])
                            right = float(parts[1]) if len(parts) > 1 else left
                            timeout = float(parts[2]) / 1000.0 if len(parts) > 2 else self.DEFAULT_TIMEOUT
                            self.move(left, right, timeout)
                elif len(path) > 2 and path[2] == "rotate":                             # mutinus/control/rotate
                    parts = msg.payload.split(" ")
                    if len(parts) > 0:
                        speed = float(parts[0])
                        timeout = float(parts[1]) / 1000.0 if len(parts) > 1 else self.DEFAULT_TIMEOUT
                        if len(path) > 3 and path[3] == "right":                        # mutinus/control/rotate/right
                            self.move(speed, -speed, timeout)
                        elif len(path) > 3 and path[3] == "left":                       # mutinus/control/rotate/left
                            self.move(-speed, speed, timeout)
                elif len(path) > 2 and path[2] == "turn":                               # mutinus/control/turn
                    parts = msg.payload.split(" ")
                    if len(parts) > 0:
                        speed = float(parts[0])
                        timeout = float(parts[1]) / 1000.0 if len(parts) > 1 else self.DEFAULT_TIMEOUT
                        if len(path) > 3 and path[3] == "right":                        # mutinus/control/turn/right
                            self.move(speed, 0, timeout)
                        elif len(path) > 3 and path[3] == "left":                       # mutinus/control/turn/left
                            self.move(0, speed, timeout / 1000.0)
                elif len(path) > 2 and path[2] == "stop":                               # mutinus/control/stop
                    self.halt()
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def move(self, left, right, timeout=DEFAULT_TIMEOUT):
        if self.timer is not None: self.timer.cancel()
        if left < -100: left = -100
        if left > 100: left = 100
        if right < -100: left = -100
        if right > 100: left = 100
        self.alphabot.set_motor(left, right)

        if self.left != left:
            self.client.publish(self.serviceName + "/state/move/left", str(left), 1, True)
        if self.right != right:
            self.client.publish(self.serviceName + "/state/move/right", str(right), 1, True)
        if self.left != left or self.right != right:
            self.client.publish(self.serviceName + "/state/move", str(left) + " " + str(right), 1, True)
            self.logger.info("Moving left at " + str(left) + "%, right at " + str(right) + "%")

        self.left = left
        self.right = right
        if timeout > 0: self.timer = threading.Timer(timeout, self.halt).start()

    def halt(self):
        self.alphabot.stop()
        if self.left != 0:
            self.client.publish(self.serviceName + "/state/move/left", "0", 1, True)
        if self.right != 0:
            self.client.publish(self.serviceName + "/state/move/right", "0", 1, True)
        if self.left != 0 or self.right != 0:
            self.client.publish(self.serviceName + "/state/move", "0 0", 1, True)
            self.logger.info("Stop moving")
        self.left = 0
        self.right = 0
