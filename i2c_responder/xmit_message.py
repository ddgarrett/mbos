"""
    General Message Transmit class.
    
    Aids building a message that is sent from one service to another.
    Supports definition of to, from and message.
    For simple messages all three values can be specified when the object is created.
    Subclasses implement more complex messages. See xmit_lcd.py for an example.
"""

import ujson

class XmitMsg:
    
    def __init__(self,fr="",to="",msg=""):
        self.to = to
        self.fr = fr
        self.msg = msg
        
    def set_to(self,service_to):
        self.to = service_to
        return self
        
    def set_from(self,service_from):
        self.fr = service_from
        return self
        
    def set_msg(self,message):
        self.msg = message
        return self
    
    def get_from(self):
        return self.fr
    
    def get_to(self):
        return self.to
    
    def get_msg(self):
        return self.msg
    # dumps will generate a string version of this object
    def dumps(self):
        message = [self.fr, self.to, type(self), self.msg]
        return ujson.dumps(message)
    
    
    