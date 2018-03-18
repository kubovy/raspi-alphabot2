#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import RPi.GPIO as GPIO
from rx import Observable, Observer
from Logger import Logger


class Ultrasonic:

    TRIG = 22
    ECHO = 27

    delay = 0
    timer = None

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.service_name = service_name
        self.logger = Logger("Ultrasonic", debug)
        self.source = Observable.interval(1000).map(lambda i: self.get_distance())

        GPIO.setup(self.TRIG, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ECHO, GPIO.IN)

        self.client.publish(self.service_name + "/state/distance/measuring", "OFF", 1, False)
        self.client.publish(self.service_name + "/state/distance/delay", "0", 1, False)
        self.client.message_callback_add(self.service_name + "/control/distance/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.service_name and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "distance":                             # mutinus/control/distance
                    if msg.payload == "" or msg.payload == "MEASURE":
                        distance = self.get_distance()
                        self.logger.info("Measuring distance: " + str(distance))
                        self.client.publish(self.service_name + "/state/distance", distance, 1, False)
                    else:
                        self.delay = 0 if (msg.payload == "OFF") else float(msg.payload)
                        if self.delay <= 0: self.delay = 0
                        self.client.publish(self.service_name + "/state/distance/delay", str(self.delay), 1, False)
                        self.logger.info("Measuring distance each " + str(self.delay) + "ms")
                        if self.delay > 0:
                            self.start()
                        else:
                            self.stop()
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def get_distance(self):
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

    def subscribe(self, on_next):
        return self.source.subscribe(
            on_next=on_next,
            on_error=lambda e: self.logger.error(str(e)),
            on_completed=lambda: self.logger.info("Subscription completed"))

    def looper(self):
        try:
            distance = self.get_distance()
            self.logger.info("Distance: " + str(distance) + "mm")
            self.client.publish(self.service_name + "/state/distance", str(distance), 1, False)
            self.timer = threading.Timer(self.delay, self.looper).start()
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def start(self, delay=None):
        if delay is not None: self.delay = delay
        if self.timer is None:
            self.client.publish(self.service_name + "/state/distance/measuring", "ON", 1, False)
            self.timer = threading.Timer(self.delay, self.looper).start()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
            self.client.publish(self.service_name + "/state/distance/measuring", "OFF", 1, False)
        self.timer = None
