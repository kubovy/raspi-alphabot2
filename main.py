#!/usr/bin/python
# -*- coding:utf-8 -*-
import multiprocessing
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
# from rx.concurrency import ThreadPoolScheduler

from neopixel import *
from AlphaBot import AlphaBot
from PCA9685 import PCA9685
from Logger import Logger
from Buzzer import Buzzer
from CameraServo import CameraServo
from InfraredReceiver import InfraredReceiver
from InfraredSensor import InfraredSensor
from Joystick import Joystick
from ObstacleAvoidance import ObstacleAvoidance
from Pixels import Pixels
from TRSensors import TRSensor
from Ultrasonic import Ultrasonic
from Wheels import Wheels

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
SERVICE_NAME = "mutinus"
DEBUG = True

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

logger = Logger("MAIN", DEBUG)

# calculate number of CPU's, then create a ThreadPoolScheduler with that number of threads
optimal_thread_count = multiprocessing.cpu_count()
# pool_scheduler = ThreadPoolScheduler(optimal_thread_count)
logger.info("Thread pool: " + str(optimal_thread_count))

# MQTT Client
mqtt = mqtt.Client("Mutinus", True, None, mqtt.MQTTv311, "tcp")  # create new instance


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")
    client.subscribe(SERVICE_NAME + "/control/#")
    client.publish(SERVICE_NAME + "/state/status", "ON", 1, True)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.error("Unexpected disconnection.")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        logger.debug(msg.topic + ": '" + str(msg.payload) + "'")
    except:
        logger.info("Error!")


mqtt.on_connect = on_connect
mqtt.on_disconnect = on_disconnect
mqtt.on_message = on_message
mqtt.will_set(SERVICE_NAME + "/state/status", "OFF", 1, True)
mqtt.reconnect_delay_set(min_delay=1, max_delay=60)
mqtt.connect(BROKER_ADDRESS, BROKER_PORT, 60)  # connect to broker
mqtt.publish(SERVICE_NAME + "/state/status", "ON", 1, True)


# Modules
pixels = Pixels(mqtt, SERVICE_NAME, DEBUG)
buzzer = Buzzer(mqtt, SERVICE_NAME, DEBUG)
cameraServo = CameraServo(mqtt, SERVICE_NAME, DEBUG)
infrared_receiver = InfraredReceiver(mqtt, SERVICE_NAME, DEBUG)
infrared_sensor = InfraredSensor(mqtt, SERVICE_NAME, DEBUG)
joystick = Joystick(mqtt, SERVICE_NAME, DEBUG)
obstacle_avoidance = ObstacleAvoidance(mqtt, SERVICE_NAME, DEBUG)
trSensor = TRSensor(mqtt, SERVICE_NAME, 5, DEBUG)
ultrasonic = Ultrasonic(mqtt, SERVICE_NAME, DEBUG)
wheels = Wheels(mqtt, SERVICE_NAME, DEBUG)

# Setup IR Sensor
infrared_receiver.buzzer = buzzer
infrared_receiver.camera_servo = cameraServo
infrared_receiver.pixels = pixels
infrared_receiver.wheels = wheels

# Setup Joystick
joystick.buzzer = buzzer
joystick.camera_servo = cameraServo
joystick.wheels = wheels

# Setup Obstacle Avoidance
obstacle_avoidance.infrared_sensor = infrared_sensor
obstacle_avoidance.ultrasonic = ultrasonic
obstacle_avoidance.wheels = wheels
#obstacle_avoidance.start()

logger.info("Press [CTRL+C] to exit")
try:
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    mqtt.loop_forever(retry_first_connection=True)
except KeyboardInterrupt:
    logger.error("Finishing up...")
except:
    logger.error("Unexpected Error!")
    traceback.print_exc()
finally:
    infrared_receiver.stop()
    infrared_sensor.stop()
    joystick.stop()
    obstacle_avoidance.stop()
    trSensor.stop()
    ultrasonic.stop()

    GPIO.cleanup()
    mqtt.publish("mutinus/state/status", "OFF", 1, True)

