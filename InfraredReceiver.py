#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import Pixels
from Logger import Logger


class InfraredReceiver:

    CONTROL = 17

    interrupted = False
    thread = None
    control = False

    pixels = None
    wheels = None
    last_action = None
    camera_servo = None
    buzzer = None

    speed = 50
    roll = 50
    pitch = 50
    light_backward = False
    timer = None

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
        self.logger = Logger("InfraredReceiver", debug)

        GPIO.setup(self.CONTROL, GPIO.IN)

        self.client.publish(self.serviceName + "/state/ir-receiver/state", "OFF", 1, True)
        self.client.publish(self.serviceName + "/state/ir-receiver/control", "OFF", 1, True)
        self.client.message_callback_add(self.serviceName + "/control/ir-receiver/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "ir-receiver":                           # mutinus/control/ir-receiver/#
                    if msg.payload == "CONTROL":
                        self.start(True)
                        if self.pixels is not None: self.pixels.notify([
                            [[0, 0, 255], [255, 0, 255], [255, 0, 255], [0, 0, 255]],
                            [[0, 255, 0], [0, 0, 0], [0, 0, 0], [0, 255, 0]]
                        ], [0.5, 1.0])
                    elif msg.payload == "ON":
                        self.start()
                        if self.pixels is not None: self.pixels.notify([
                            [[0, 0, 255], [0, 0, 0], [0, 0, 0], [0, 0, 255]],
                            [[0, 255, 0], [0, 0, 0], [0, 0, 0], [0, 255, 0]]
                        ], [0.5, 1.0])
                    else:
                        self.stop()
                        if self.pixels is not None: self.pixels.notify([
                            [[0, 0, 255], [0, 0, 0], [0, 0, 0], [0, 0, 255]],
                            [[255, 0, 0], [0, 0, 0], [0, 0, 0], [255, 0, 0]]
                        ], [0.5, 1.0])
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def get_key(self):
        if GPIO.input(self.CONTROL) == 0:
            count = 0
            while GPIO.input(self.CONTROL) == 0 and count < 200:        # 9ms
                count += 1
                time.sleep(0.00006)
            if count < 10:
                return
            count = 0
            while GPIO.input(self.CONTROL) == 1 and count < 80:         # 4.5ms
                count += 1
                time.sleep(0.00006)

            idx = 0
            cnt = 0
            data = [0, 0, 0, 0]
            for i in range(0, 32):
                count = 0
                while GPIO.input(self.CONTROL) == 0 and count < 15:     # 0.56ms
                    count += 1
                    time.sleep(0.00006)

                count = 0
                while GPIO.input(self.CONTROL) == 1 and count < 40:     # 0: 0.56mx
                    count += 1                                          # 1: 1.69ms
                    time.sleep(0.00006)

                if count > 7:
                    data[idx] |= 1<<cnt
                if cnt == 7:
                    cnt = 0
                    idx += 1
                else:
                    cnt += 1
            # self.logger.debug(str(data))
            if data[0] + data[1] == 0xFF and data[2] + data[3] == 0xFF:  # check
                return data[2]
            else:
                return 0xFF  # "repeat"

    def perform(self, action):
        self.logger.info("Performing: " + str(action))
        if action == "MOVE_FORWARD":
            if self.wheels is not None: self.wheels.move(self.speed, self.speed, 0.5)
            self.last_action = action
        elif action == "MOVE_BACKWARD":
            if self.wheels is not None: self.wheels.move(-self.speed, -self.speed, 0.5)
            self.last_action = action
        elif action == "ROTATE_LEFT":
            if self.wheels is not None: self.wheels.move(self.speed, -self.speed, 0.1)
            self.last_action = action
        elif action == "ROTATE_RIGHT":
            if self.wheels is not None: self.wheels.move(-self.speed, self.speed, 0.1)
            self.last_action = action
        elif action == "TURN_LEFT":
            if self.wheels is not None: self.wheels.move(self.speed, 0, 0.25)
            self.last_action = action
        elif action == "TURN_RIGHT":
            if self.wheels is not None: self.wheels.move(0, self.speed, 0.25)
            self.last_action = action
        elif action == "TURN_BACK_LEFT":
            if self.wheels is not None: self.wheels.move(-self.speed, 0, 0.25)
            self.last_action = action
        elif action == "TURN_BACK_RIGHT":
            if self.wheels is not None: self.wheels.move(0, -self.speed, 0.25)
            self.last_action = action
        elif action == "SPEED_DECREASE":
            self.speed += 5
            if self.speed > 100: self.speed = 100
            self.last_action = action
        elif action == "SPEED_INCREASE":
            self.speed -= 5
            if self.speed < 0: self.speed = 10
            self.last_action = action
        elif action == "STOP":
            self.perform("LIGHT_BREAK")
            if self.wheels is not None: self.wheels.halt()
            self.last_action = action
        elif action == "ROLL_LEFT":
            self.roll -= 5
            if self.camera_servo is not None: self.camera_servo.roll_percent(self.roll)
            self.last_action = action
        elif action == "ROLL_RIGHT":
            self.roll += 5
            if self.camera_servo is not None: self.camera_servo.roll_percent(self.roll)
            self.last_action = action
        elif action == "PITCH_UP":
            self.pitch += 5
            if self.camera_servo is not None: self.camera_servo.pitch_percent(self.pitch)
            self.last_action = action
        elif action == "PITCH_DOWN":
            self.pitch -= 5
            if self.camera_servo is not None: self.camera_servo.pitch_percent(self.pitch)
            self.last_action = action
        elif action == "BLINK_LEFT":
            self.last_action = action
            if self.pixels is not None: self.pixels.notify([
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 128, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 128, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 128, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [255, 128, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            ], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        elif action == "BLINK_RIGHT":
            if self.pixels is not None: self.pixels.notify([
                [[255, 128, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[255, 128, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[255, 128, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[255, 128, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            ], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
            self.last_action = action
        elif action == "LIGHT_BREAK":
            if self.pixels is not None: self.pixels.notify([[[255, 0, 0], [0, 0, 0], [0, 0, 0], [255, 0, 0]]], [1])
            self.last_action = action
        elif action == "LIGHT_BACKWARD":
            if self.pixels is not None:
                if self.light_backward:
                    self.pixels.set_color(0, 0, 0, 0)
                    self.pixels.set_color(1, 0, 0, 0)
                    self.pixels.set_color(2, 0, 0, 0)
                    self.pixels.set_color(3, 0, 0, 0)
                    self.light_backward = False
                else:
                    self.pixels.set_color(0, 0, 0, 0)
                    self.pixels.set_color(1, 255, 255, 255)
                    self.pixels.set_color(2, 255, 255, 255)
                    self.pixels.set_color(3, 0, 0, 0)
                    self.light_backward = True
            self.last_action = None
        elif action == "BUZZER":
            if self.buzzer is not None: self.buzzer.beep(0.5)
            self.last_action = action
        elif action == "REPEAT":
            self.perform(self.last_action)
        elif action == "NO_INPUT":
            if self.wheels is not None: self.wheels.halt()
            self.last_action = None

    def looper(self):
        while not self.interrupted:
            try:
                if self.on:
                    key = self.get_key()
                    if key is not None:
                        if self.timer is not None:
                            self.timer.cancel()
                            self.timer = None
                        self.logger.info("Key: " + str(key))
                        self.client.publish(self.serviceName + "/state/ir-receiver", key, 1, False)
                        if self.control:
                            if key == 69: self.perform("ROLL_LEFT")         # CH-
                            elif key == 70: self.perform("PITCH_UP")        # CH
                            elif key == 71: self.perform("ROLL_RIGHT")      # CH+
                            elif key == 68: self.perform("BLINK_LEFT")      # PREV
                            elif key == 64: self.perform("PITCH_DOWN")      # NEXT
                            elif key == 67: self.perform("BLINK_RIGHT")     # PLAY/PAUSE
                            elif key == 7:  self.perform("SPEED_DECREASE")  # VOL-
                            elif key == 21: self.perform("SPEED_INCREASE")  # VOL+
                            elif key == 9:  self.perform("BUZZER")          # EQ
                            elif key == 25: self.perform("LIGHT_BREAK")     # 100+
                            elif key == 13: self.perform("LIGHT_BACKWARD")  # 200+
                            elif key == 12: self.perform("TURN_LEFT")       # 1
                            elif key == 24: self.perform("MOVE_FORWARD")    # 2
                            elif key == 94: self.perform("TURN_RIGHT")      # 3
                            elif key == 8:  self.perform("ROTATE_LEFT")     # 4
                            elif key == 28: self.perform("STOP")            # 5
                            elif key == 90: self.perform("ROTATE_RIGHT")    # 6
                            elif key == 66: self.perform("TURN_BACK_LEFT")  # 7
                            elif key == 82: self.perform("MOVE_BACKWARD")   # 8
                            elif key == 74: self.perform("TURN_BACK_RIGHT") # 9
                            elif key == 255: self.perform("REPEAT")         # Repeat
                        self.timer = threading.Timer(1.0, self.cancel).start()

                else:
                    time.sleep(1.0)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
        self.logger.info("Exiting looper")

    def cancel(self):
        self.perform("NO_INPUT")

    def start(self, control=False):
        if self.thread is None:
            self.client.publish(self.serviceName + "/state/ir-receiver/state", "ON", 1, True)
            if not control: self.client.publish(self.serviceName + "/state/ir-receiver/control", "ON", 1, True)
            self.control = control
            self.interrupted = False
            self.thread = threading.Thread(target=self.looper)
            self.thread.start()
        return self.thread

    def stop(self):
        self.interrupted = True
        if self.thread is not None:
            self.client.publish(self.serviceName + "/state/ir-receiver/state", "OFF", 1, True)
            if self.control: self.client.publish(self.serviceName + "/state/ir-receiver/control", "OFF", 1, True)
            self.control = False
            self.thread.join(5)
        self.thread = None
