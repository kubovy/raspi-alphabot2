#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

from neopixel import *
from AlphaBot import AlphaBot
from PCA9685 import PCA9685
from Logger import Logger
from Buzzer import Buzzer
from CameraServo import CameraServo
from IRSensor import IRSensor
from Joystick import Joystick
from Pixels import Pixels
from TRSensors import TRSensor
from Ultrasonic import Ultrasonic
from Wheels import Wheels


BROKER_ADDRESS = "localhost" #192.168.10.6" 
BROKER_PORT = 1883
SERVICE_NAME = "mutinus"
DEBUG = True

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

logger = Logger("MAIN", DEBUG)

# MQTT Client
client = mqtt.Client("Mutinus", True, None, mqtt.MQTTv311, "tcp") #create new instance

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")
    client.subscribe(SERVICE_NAME + "/control/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        logger.debug(msg.topic + ": '" + str(msg.payload) + "'")
    except:
        logger.info("Error!")

client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_ADDRESS, BROKER_PORT, 60) #connect to broker
client.publish("mutinus/state/status","ON", 1, True)

# Modules
buzzer = Buzzer(client, SERVICE_NAME, DEBUG)
cameraServo = CameraServo(client, SERVICE_NAME, DEBUG)
irSensor = IRSensor(client, SERVICE_NAME, DEBUG)
joystick = Joystick(client, SERVICE_NAME, DEBUG)
pixels = Pixels(client, SERVICE_NAME, DEBUG)
trSensor = TRSensor(client, SERVICE_NAME, 5, DEBUG)
ultrasonic = Ultrasonic(client, SERVICE_NAME, DEBUG)
wheels = Wheels(client, SERVICE_NAME, DEBUG)

# Threads
cameraServo.start()
irSensor.start()
joystick.start()
trSensor.start()
ultrasonic.start()
wheels.start()

logger.info("Press [CTRL+C] to exit")
try:
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()
except KeyboardInterrupt:
    logger.error("Finishing up...")
except:
    logger.error("Unexpected Error!")
    traceback.print_exc()
finally:
    cameraServo.stop()
    irSensor.stop()
    joystick.stop()
    trSensor.stop()
    ultrasonic.stop()
    wheels.stop()

    GPIO.cleanup()
    client.publish("mutinus/state/status","OFF", 1, True)

