import time

class Logger:
    def __init__(self, name, debug = False):
        self.name = name
        self.isDebugging = debug
        
    def debug(self, message):
        if (self.isDebugging): print(time.ctime() + " DEBUG [" + self.name + "]: " + message) 

    def info(self, message):
            print(time.ctime() + " INFO [" + self.name + "]: " + message)
        
    def error(self, message):
            print(time.ctime() + " ERROR [" + self.name + "]: " + message)
        
