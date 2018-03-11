#!/usr/bin/python
import time
import math
import smbus
from Logger import Logger

# ============================================================================
# Raspi PCA9685 16-Channel PWM Servo Driver
# ============================================================================

class PCA9685:

    # Registers/etc.
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __MODE1              = 0x00
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALLLED_ON_L        = 0xFA
    __ALLLED_ON_H        = 0xFB
    __ALLLED_OFF_L       = 0xFC
    __ALLLED_OFF_H       = 0xFD
    
    freq = 50

    def __init__(self, address=0x40, debug=False):
        self.bus = smbus.SMBus(1)
        self.address = address
        self.logger = Logger("PCA9658", debug)
        self.logger.debug("Reseting PCA9685")
        self.write(self.__MODE1, 0x00)
	
    def write(self, reg, value):
        "Writes an 8-bit value to the specified register/address"
        self.bus.write_byte_data(self.address, reg, value)
        self.logger.debug("I2C: Write 0x%02X to register 0x%02X" % (value, reg))
	  
    def read(self, reg):
        "Read an unsigned byte from the I2C device"
        result = self.bus.read_byte_data(self.address, reg)
        self.logger.debug("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
        return result

    def setPWMFreq(self, freq):
        "Sets the PWM frequency"
        self.freq = freq
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        self.logger.debug("Setting PWM frequency to %d Hz" % freq)
        self.logger.debug("Estimated pre-scale: %d" % prescaleval)
        prescale = math.floor(prescaleval + 0.5)
        self.logger.debug("Final pre-scale: %d" % prescale)

        oldmode = self.read(self.__MODE1);
        newmode = (oldmode & 0x7F) | 0x10        # sleep
        self.write(self.__MODE1, newmode)        # go to sleep
        self.write(self.__PRESCALE, int(math.floor(prescale)))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def setPWM(self, channel, on, off):
        "Sets a single PWM channel"
        self.write(self.__LED0_ON_L+4*channel, on & 0xFF)
        self.write(self.__LED0_ON_H+4*channel, on >> 8)
        self.write(self.__LED0_OFF_L+4*channel, off & 0xFF)
        self.write(self.__LED0_OFF_H+4*channel, off >> 8)
        self.logger.debug("channel: %d  LED_ON: %d LED_OFF: %d" % (channel,on,off))
            
    def setServoPulse(self, channel, pulse):
        "Sets the Servo Pulse,The PWM frequency must be 50HZ"
        pulse = pulse * 4096 * self.freq / 1000000# pulse * 4096 / 20000        #PWM frequency is 50HZ,the period is 20000us
        self.setPWM(channel, 0, pulse)
        
    def stop(self, channel):
        self.logger.debug("Stopping PCA9685")
        self.write(self.__MODE1, 0x00)
        self.write(self.__PRESCALE, 0x00)
        self.setPWM(channel, 0, 0)
    

if __name__=='__main__':
 
    pwm = PCA9685(0x40, debug=True)
    pwm.setPWMFreq(50)
    while True:
    # setServoPulse(2,2500)
        for i in range(500,2500,10):  
            pwm.setServoPulse(0,i)   
            time.sleep(0.02)     
        
        for i in range(2500,500,-10):
            pwm.setServoPulse(0,i) 
            time.sleep(0.02)  
