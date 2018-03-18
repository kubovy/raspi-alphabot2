#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
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

    on = False
    control = "NONE"

    roll = 50
    pitch = 50
    camera_servo = None
    wheels = None
    buzzer = None

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
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

        self.client.publish(self.serviceName + "/state/joystick/state", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/joystick/control", "NONE", 1, True)
        self.client.message_callback_add(self.serviceName + "/control/joystick/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "joystick":                             # mutinus/control/joystick/#
                    if len(path) > 3 and path[3] == "state":
                        if msg.payload == "ON":
                            if not self.on: self.client.publish(self.serviceName + "/state/joystick/state", "ON", 1, True)
                            self.on = True
                            self.start()
                        else:
                            if self.on: self.client.publish(self.serviceName + "/state/joystick/state", "OFF", 1, True)
                            if self.control != "NONE": self.client.publish(self.serviceName + "/state/joystick/control", "NONE", 1, True)
                            self.on = False
                            self.stop()
                    elif len(path) > 3 and path[3] == "control":
                        if msg.payload == "MOVEMENT":
                            if not self.on: self.client.publish(self.serviceName + "/state/joystick/state", "ON", 1, True)
                            if self.control != "MOVEMENT": self.client.publish(self.serviceName + "/state/joystick/control", "MOVEMENT", 1, True)
                            self.on = True
                            self.control = "MOVEMENT"
                            self.start()
                        elif msg.payload == "CAMERA":
                            if not self.on: self.client.publish(self.serviceName + "/state/joystick/state", "ON", 1, True)
                            if self.control != "CAMERA": self.client.publish(self.serviceName + "/state/joystick/control", "CAMERA", 1, True)
                            self.on = True
                            self.control = "CAMERA"
                            self.start()
                        else:
                            if self.on: self.client.publish(self.serviceName + "/state/joystick/state", "OFF", 1, True)
                            if self.control != "NONE": self.client.publish(self.serviceName + "/state/joystick/control", "NONE", 1, True)
                            self.on = False
                            self.control = "NONE"
                            self.stop()

        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def looper(self):
        while not self.interrupted:
            try:
                if GPIO.input(self.CTR) == 0:
                    if self.state != self.CTR:
                        self.logger.info("CENTER")
                        self.client.publish(self.serviceName + "/state/joystick", "CENTER", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/center", "ON", 1, True)
                        self.state = self.CTR
                    if self.control == "CAMERA" and self.camera_servo is not None:
                        if self.buzzer is not None: self.buzzer.on()
                    if self.control == "MOVEMENT" and self.wheels is not None:
                        self.wheels.halt()
                        if self.buzzer is not None: self.buzzer.on()
                elif GPIO.input(self.A) == 0:
                    if self.state != self.A:
                        self.logger.info("UP")
                        self.client.publish(self.serviceName + "/state/joystick", "UP", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/up", "ON", 1, True)
                        self.state = self.A
                    if self.control == "CAMERA" and self.camera_servo is not None:
                        self.pitch += 5
                        self.camera_servo.pitch_percent(self.pitch)
                    elif self.control == "MOVEMENT" and self.wheels is not None:
                        self.wheels.move(50, 50, 1.0)
                elif GPIO.input(self.B) == 0:
                    if self.state != self.B:
                        self.logger.info("RIGHT")
                        self.client.publish(self.serviceName + "/state/joystick", "RIGHT", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/right", "ON", 1, True)
                        self.state = self.B
                    if self.control == "CAMERA" and self.camera_servo is not None:
                        self.roll += 5
                        self.camera_servo.roll_percent(self.roll)
                    elif self.control == "MOVEMENT" and self.wheels is not None:
                        self.wheels.move(-50, 50, 1.0)
                elif GPIO.input(self.C) == 0:
                    if self.state != self.D:
                        self.logger.info("LEFT")
                        self.client.publish(self.serviceName + "/state/joystick", "LEFT", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/left", "ON", 1, True)
                        self.state = self.D
                    if self.control == "CAMERA" and self.camera_servo is not None:
                        self.roll -= 5
                        self.camera_servo.roll_percent(self.roll)
                    elif self.control == "MOVEMENT" and self.wheels is not None:
                        self.wheels.move(50, -50, 1.0)
                elif GPIO.input(self.D) == 0:
                    if self.state != self.C:
                        self.logger.info("DOWN")
                        self.client.publish(self.serviceName + "/state/joystick", "DOWN", 1, True)
                        self.client.publish(self.serviceName + "/state/joystick/down", "ON", 1, True)
                        self.state = self.C
                    if self.control == "CAMERA" and self.camera_servo is not None:
                        self.pitch -= 5
                        self.camera_servo.pitch_percent(self.pitch)
                    elif self.control == "MOVEMENT" and self.wheels is not None:
                        self.wheels.move(-50, -50, 1.0)
                else:
                    if self.state != self.NONE:
                        self.logger.info("NONE")
                        self.client.publish(self.serviceName + "/state/joystick", "NONE", 1, True)
                        if self.state == self.CTR: self.client.publish(self.serviceName + "/state/joystick/center", "OFF", 1, True)
                        elif self.state == self.A: self.client.publish(self.serviceName + "/state/joystick/up", "OFF", 1, True)
                        elif self.state == self.B: self.client.publish(self.serviceName + "/state/joystick/right", "OFF", 1, True)
                        elif self.state == self.C: self.client.publish(self.serviceName + "/state/joystick/down", "OFF", 1, True)
                        elif self.state == self.D: self.client.publish(self.serviceName + "/state/joystick/left", "OFF", 1, True)
                        self.state = self.NONE
                        if self.buzzer is not None: self.buzzer.off()
                        if self.wheels is not None: self.wheels.halt()

                time.sleep(0.2)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
        self.logger.info("Exiting looper")

    def start(self):
        if self.thread is None:
            self.interrupted = False
            self.thread = threading.Thread(target=self.looper)
            self.thread.start()
        return self.thread

    def stop(self):
        self.interrupted = True
        if self.thread is not None: self.thread.join(5)
        self.thread = None
