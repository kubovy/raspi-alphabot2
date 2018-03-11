#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from Logger import Logger

class Buzzer:

    BUZZER = 4

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("Buzzer", debug)

        self.client.message_callback_add(self.serviceName + "/control/buzzer/#", self.on_message)

        GPIO.setup(self.BUZZER, GPIO.OUT)
        self.off()
       
    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if (len(path) > 1 and path[0] == self.serviceName and path[1] == "control"): # mutinus/control/#
                if (len(path) > 2 and path[2] == "buzzer"):                              # mutinus/control/buzzer
                    self.logger.info(msg.payload)
                    if (msg.payload == "ON"):
                        self.on()
                    else:
                        self.off()
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def on(self):
        GPIO.output(self.BUZZER, GPIO.HIGH)
        self.client.publish(self.serviceName + "/state/buzzer", "ON", 1, True)

    def off(self):
        GPIO.output(self.BUZZER, GPIO.LOW)
        self.client.publish(self.serviceName + "/state/buzzer", "OFF", 1, True)
