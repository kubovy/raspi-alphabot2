#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import threading
import traceback
from rx import Observable, Observer
from Logger import Logger


class InfraredSensor:

    DR = 16
    DL = 19

    interrupted = False
    thread = None
    on = False
    left = 1
    right = 1

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
        self.logger = Logger("InfraredSensor", debug)
        self.source = Observable.interval(50).map(lambda i: self.get_state())

        GPIO.setup(self.DR, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.DL, GPIO.IN, GPIO.PUD_UP)

        self.client.publish(self.serviceName + "/state/ir-sensor/state", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/ir-sensor/state/left", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/ir-sensor/state/right", "OFF", 1, True)
        self.client.message_callback_add(self.serviceName + "/control/ir-sensor/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "ir-sensor":                            # mutinus/control/ir-sensor
                    self.logger.info(msg.payload)
                    if msg.payload == "ON":
                        self.start()
                    else:
                        self.stop()


        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def get_state(self):
        left = GPIO.input(self.DL)
        right = GPIO.input(self.DR)
        return [left, right]

    def subscribe(self, on_next):
        return self.source.subscribe(
            on_next=on_next,
            on_error=lambda e: self.logger.error(str(e)),
            on_completed=lambda: self.logger.info("Subscription completed"))

    def looper(self):
        while not self.interrupted:
            try:
                state = self.get_state()
                self.logger.debug("Left: " + str(state[0]) + ", Right: " + str(state[1]))
                if state[0] != self.left:
                    self.left = state[0]
                    payload = "ON" if self.left == 0 else "OFF"
                    self.client.publish(self.serviceName + "/state/ir-sensor/left", payload, 0, False)
                if state[1] != self.right:
                    self.right = state[1]
                    payload = "ON" if self.right == 0 else "OFF"
                    self.client.publish(self.serviceName + "/state/ir-sensor/right", payload, 0, False)

                time.sleep(0.05)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
        self.logger.info("Exiting looper")

    def start(self):
        if self.thread is not None:
            self.client.publish(self.serviceName + "/state/ir-sensor", "ON", 1, True)
            self.interrupted = False
            self.thread = threading.Thread(target=self.looper)
            self.thread.start()
        return self.thread

    def stop(self):
        self.interrupted = True
        if self.thread is not None:
            self.client.publish(self.serviceName + "/state/ir-sensor", "OFF", 1, True)
            self.thread.join(5)
        self.thread = None