#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import threading
from Logger import Logger


MODE_RUNNING = "RUNNING"
MODE_TURNING_LEFT = "TURNING_LEFT"
MODE_TURNING_RIGHT = "TURNING_RIGHT"
MODE_CHECK_SPACE = "CHECK_SPACE"

RUNNING_SPEEDS       = [ 10,  30,   50,   75,   85, 100]
RUNNING_DISTANCES    = [200, 500, 1000, 2000, 2500]
TURNING_DISTANCE_MIN = 800.0  # mm
TURNING_SPEED        = 30

CHECK_SPEED            = 30
CHECK_INTERVAL         = 0.09
CHECK_ROUND_ITERATIONS = 26


class ObstacleAvoidance:

    # interrupted = False
    # thread = None

    distance = -1
    left = -1
    right = -1
    left_timestamp = -1
    right_timestamp = -1

    infrared_sensor = None
    ultrasonic = None
    wheels = None

    infrared_subscription = None
    ultrasonic_subscription = None

    left_speed = 30
    right_speed = 30
    interval = 0
    mode = MODE_RUNNING
    iterations = -1
    distances = []
    last_distance = -1

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
        self.logger = Logger("ObstacleAvoidance", debug)

        self.client.publish(self.serviceName + "/state/obstacle-avoidance", "OFF", 1, True)
        self.client.message_callback_add(self.serviceName + "/control/obstacle-avoidance/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control":  # mutinus/control/#
                if len(path) > 2 and path[2] == "obstacle-avoidance":                   # mutinus/control/obstacle-avoidance/#
                    if msg.payload == "ON":
                        self.start()
                    else:
                        self.stop()
        except:
            self.logger.error("Unexpected Error!")

    def on_infrared_distance(self, state):
        left = state[0]
        right = state[1]
        if self.left != left or self.right != right:
            self.logger.info("Left: " + str(left) + ", Right: " + str(right))
        if self.left != left:
            self.left_timestamp = time.time() if left == 0 else -1
            self.left = left
        if self.right != right:
            self.right_timestamp = time.time() if right == 0 else -1
            self.right = right
        if not self.mode.startswith("CHECK_"): self.update_wheels()

    def on_ultrasonic_distance(self, distance):
        if self.distance != distance:
            self.logger.info("Distance: " + str(distance))
            self.distance = distance
        if not self.mode.startswith("CHECK_"): self.update_wheels()

    def update_wheels(self):
        if self.mode == MODE_RUNNING and (self.left == 0 or self.right == 0):
            self.left_speed = self.right_speed = 0
            self.interval = 0
            self.mode = MODE_TURNING_RIGHT if self.left_timestamp > self.right_timestamp else MODE_TURNING_LEFT
            self.logger.info("Mode: " + self.mode + ", Left time:" + str(self.left_timestamp) + ", Right time: " + str(self.right_timestamp))
        elif self.mode == MODE_RUNNING:
            speed = RUNNING_SPEEDS[-1]
            for i in range(0, len(RUNNING_DISTANCES)):
                if self.distance < RUNNING_DISTANCES[i]:
                    speed = RUNNING_SPEEDS[i]
                    break
            self.left_speed = self.right_speed = speed
            self.interval = 0
        elif self.mode == MODE_TURNING_LEFT and self.left == 1 and self.right == 1 and self.distance > TURNING_DISTANCE_MIN:
            self.left_speed = self.right_speed = 10
            self.interval = 0
            self.mode = MODE_RUNNING
            self.logger.info("Mode: " + self.mode + ", Left: " + str(self.left) + ", Right: " + str(self.right))
        elif self.mode == MODE_TURNING_LEFT:
            self.left_speed = -TURNING_SPEED
            self.right_speed = TURNING_SPEED
            self.interval = 0.5
        elif self.mode == MODE_TURNING_RIGHT and self.left == 1 and self.right == 1 and self.distance > TURNING_DISTANCE_MIN:
            self.left_speed = self.right_speed = 10
            self.interval = 0
            self.mode = MODE_RUNNING
            self.logger.info("Mode: " + self.mode + ", Left: " + str(self.left) + ", Right: " + str(self.right))
        elif self.mode == MODE_TURNING_RIGHT:
            self.left_speed = TURNING_SPEED
            self.right_speed = -TURNING_SPEED
            self.interval = 0.5
        elif self.mode == MODE_CHECK_SPACE:
            if self.iterations < 0:
                self.distances = []
                self.iterations = 0
            self.logger.info("Mode: " + self.mode + ", Iterations: " + str(self.iterations))
            distance = self.distance
            if self.iterations > CHECK_ROUND_ITERATIONS * 2:  # Rounds finished
                self.iterations = -1
                self.left_speed = self.right_speed = 0
                self.interval = 0
                self.mode = "STOP"
            elif self.last_distance != distance:  # Distance acquired
                self.left_speed = CHECK_SPEED
                self.right_speed = -CHECK_SPEED
                self.interval = CHECK_INTERVAL
                self.iterations += 1
                self.last_distance = distance
                self.distances.append(distance)
                threading.Timer(1.0, self.update_wheels).start()
            else: # Distance not acquired, try again
                self.left_speed = self.right_speed = 0
                self.interval = 0
                threading.Timer(1.0, self.update_wheels).start()
        else:
            self.logger.info("Mode: " + self.mode + ", Left speed: " + str(self.left_speed) + ", Right speed: " + str(self.right_speed))

        # self.logger.info("Updating: " + self.mode + ", Left: " + str(self.left) + ", Right: " + str(self.right) + ", Distance: " + str(self.distance))
        if self.wheels is not None: self.wheels.move(self.left_speed, self.right_speed, self.interval)

    # def looper(self):
    #    while not self.interrupted:
    #        try:
    #            time.sleep(0.5)
    #        except:
    #            self.logger.error("Unexpected Error!")

    def start(self):
        # if self.thread is None:
        #    self.interrupted = False
        #    self.thread = threading.Thread(target=self.looper)
        #    self.thread.start()
        self.client.publish(self.serviceName + "/state/obstacle-avoidance", "ON", 1, True)
        if self.infrared_subscription is None and self.infrared_sensor is not None:
            self.infrared_subscription = self.infrared_sensor.subscribe(lambda state: self.on_infrared_distance(state))
        if self.ultrasonic_subscription is None and self.ultrasonic is not None:
            self.ultrasonic_subscription = self.ultrasonic.subscribe(self.on_ultrasonic_distance)
        # return self.thread
        # self.update_wheels()

    def stop(self):
        # self.interrupted = True
        # if self.thread is not None:
        #    self.thread.join(5)
        # self.thread = None
        self.client.publish(self.serviceName + "/state/obstacle-avoidance", "OFF", 1, True)
        if self.infrared_subscription is not None:
            self.infrared_subscription.dispose()
            self.infrared_subscription = None
        if self.ultrasonic_subscription is not None:
            self.ultrasonic_subscription.dispose()
            self.ultrasonic_subscription = None
        if self.wheels is not None: self.wheels.halt()
