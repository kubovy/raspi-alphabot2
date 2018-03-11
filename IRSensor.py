#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import time
import threading
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from Logger import Logger

class IRSensor:
    
    CONTROL = 17
    
    interrupted = False
    thread = None

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("IRSensor", debug)

        GPIO.setup(self.CONTROL, GPIO.IN)
    
    def getKey(self):
        if GPIO.input(self.CONTROL) == 0:
            count = 0
            while GPIO.input(self.CONTROL) == 0 and count < 200:  #9ms
                count += 1
                time.sleep(0.00006)
            if(count < 10):
                return;
            count = 0
            while GPIO.input(self.CONTROL) == 1 and count < 80:  #4.5ms
                count += 1
                time.sleep(0.00006)

            idx = 0
            cnt = 0
            data = [0,0,0,0]
            for i in range(0,32):
                count = 0
                while GPIO.input(self.CONTROL) == 0 and count < 15:    #0.56ms
                    count += 1
                    time.sleep(0.00006)

                count = 0
                while GPIO.input(self.CONTROL) == 1 and count < 40:   #0: 0.56mx
                    count += 1                               #1: 1.69ms
                    time.sleep(0.00006)

                if count > 7:
                    data[idx] |= 1<<cnt
                if cnt == 7:
                    cnt = 0
                    idx += 1
                else:
                    cnt += 1
            self.logger.debug(str(data))
            if data[0] + data[1] == 0xFF and data[2] + data[3] == 0xFF:  #check
                return data[2]
            else:
                return 0xFF#"repeat"
        
    def looper(self):
        while self.interrupted == False:
            try:
                key = self.getKey()
                if (key != None):
                    self.logger.debug("Key: " + str(key))
                    self.client.publish(self.serviceName + "/state/ir", key, 1, False)
            except:
                self.logger.error("Unexpected Error!")
                traceback.print_exc()
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
