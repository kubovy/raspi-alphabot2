#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import threading
import traceback
import paho.mqtt.client as mqtt
from neopixel import *
from Logger import Logger

COLOR_BLACK = Color(0, 0, 0)
COLOR_WHITE = Color(255, 255, 255)
COLOR_RED = Color(255, 0, 0)
COLOR_GREEN = Color(0, 255, 0)
COLOR_BLUE = Color(0, 0, 255)
COLOR_MAGENTA = Color(255, 0, 255)


def to_color(config):
    return Color(config[0], config[1], config[2])


def to_colors(configs):
    return [to_color(configs[0]), to_color(configs[2]), to_color(configs[3]), to_color(configs[3])]


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

    pixels = [Color(0, 0, 0), Color(0, 0, 0), Color(0, 0, 0), Color(0, 0, 0)]
    notify_configs = []
    notify_delays = []

    def __init__(self, client, service_name, debug=False):
        self.client = client
        self.serviceName = service_name
        self.logger = Logger("Pixels", debug)

        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL, self.LED_STRIP)

        self.client.message_callback_add(self.serviceName + "/control/led/#", self.on_message)

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + ": " + msg.payload)
        try:
            path = msg.topic.split("/")
            if len(path) > 1 and path[0] == self.serviceName and path[1] == "control": # mutinus/control/#
                if len(path) > 2 and path[2] == "led":                                 # mutinus/control/led
                    if len(path) > 3:                                                  # mutinus/control/led/[PIXEL]
                        rgb = msg.payload.split(",")
                        self.set_color(int(path[3]), int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    else:
                        rgbs = msg.payload.split(" ")
                        for pixel in range(0, 4):
                            if len(rgbs) > pixel:
                                rgb = rgbs[pixel].split(",")
                                self.set_color(pixel, int(rgb[0]), int(rgb[1]), int(rgb[2]))
        except:
            self.logger.error("Unexpected Error!")
            traceback.print_exc()

    def notify(self, configs, delays):
        self.notify_configs = configs
        self.notify_delays = delays
        threading.Thread(target=self.notify_runnable).start()

    def notify_runnable(self):
        for i in range(len(self.notify_configs)):
            self.update(to_colors(self.notify_configs[i]))
            j = i if (i < len(self.notify_delays)) else len(self.notify_delays) - 1
            delay = self.notify_delays[j] if (j >= 0) else 1
            time.sleep(delay)
        self.notify_configs = []
        self.notify_delays = []
        self.restore()

    def restore(self):
        self.update(self.pixels)

    def update(self, pixels):
        self.strip.begin()
        for pixel in range(len(pixels)):
            color = pixels[pixel]
            self.strip.setPixelColor(pixel, color)
            # white = (color & (255 << 24)) >> 24
            red = (color & (255 << 16)) >> 16
            green = (color & (255 << 8)) >> 8
            blue = (color & 255)
            self.logger.debug("Updating " + str(pixel) + " to " + str(red) + "," + str(green) + "," + str(blue))
            self.client.publish(self.serviceName + "/state/led/" + str(pixel), str(red) + "," + str(green) + "," + str(blue), 1, True)
        self.strip.show()

    def set_color(self, pixel, red, green, blue):
        self.logger.debug("Setting " + str(pixel) + " to " + str(red) + "," + str(green) + "," + str(blue))
        self.pixels[pixel] = Color(red, green, blue)
        self.update(self.pixels)
