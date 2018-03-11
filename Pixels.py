#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
import paho.mqtt.client as mqtt
from neopixel import *
from Logger import Logger

class Pixels:
    
    # Neopixel
    LED_COUNT      = 4      # Number of LED pixels.
    LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
    LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
    LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL    = 0
    LED_STRIP      = ws.WS2811_STRIP_GRB

    pixels=[Color(0,0,0), Color(0,0,0), Color(0,0,0), Color(0,0,0)]

    def __init__(self, client, serviceName, debug=False):
        self.client = client
        self.serviceName = serviceName
        self.logger = Logger("Pixels", debug)
        
        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL, self.LED_STRIP)

        self.client.message_callback_add(self.serviceName + "/control/led/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if (len(path) > 1 and path[0] == self.serviceName and path[1] == "control"): # mutinus/control/#
                if (len(path) > 2 and path[2] == "led"):                                 # mutinus/control/led
                    if (len(path) > 3):                                                  # mutinus/control/led/[PIXEL]
                        rgb = msg.payload.split(",")
                        self.set(int(path[3]), int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    else:
                        rgbs = msg.payload.split(" ")
                        for pixel in range(0, 4):
                            if (len(rgbs) > pixel):
                                rgb = rgbs[pixel].split(",")
                                self.set(pixel, int(rgb[0]), int(rgb[1]), int(rgb[2]))
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def update(self):
        self.strip.begin()
        for pixel in range(0, 4):
            color = self.pixels[pixel]
            self.strip.setPixelColor(pixel, color)
            white = (color & (255 << 24)) >> 24
            red = (color & (255 << 16)) >> 16
            green = (color & (255 << 8)) >> 8
            blue = (color & 255)
            self.client.publish(self.serviceName + "/state/led/" + str(pixel), str(red) + "," + str(green) + "," + str(blue), 1, True)
        self.strip.show()


    def set(self, pixel, red, green, blue):
        self.pixels[pixel] = Color(red, green, blue)
        self.update()
