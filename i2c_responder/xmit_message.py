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
        message = [self.fr, self.to, str(type(self)), self.msg]
        # message = [self.fr, self.to, self.msg]
        return ujson.dumps(message)
    
    # wrap a message in a new to/from xmit
    def wrapXmit(self, fr=None,to=None):
        if fr == None:
            fr = self.fr
            
        if to == None:
            to = self.to
            
        new_msg = self.dumps()
        return XmitMsg(fr=fr,to=to,msg=new_msg)
    
    # unwrap a previous wrapped message
    def unwrapMsg(self):
        xmit_data = ujson.loads(self.msg)
        self.fr = xmit_data[0]
        self.to = xmit_data[1]
        # for now, ignore xmit type
        # they should just be to help build an xmit
        
        """
        if xmit_data[2] == "<class 'XmitLcd'>":
            self.msg = ujson.loads(xmit_data[3])
        else:
            self.msg = xmit_data[3]
        """
        
        self.msg = xmit_data[3]
        
        return self
            
        # print("type xmit_data[2]" + str(type(xmit_data[2])))
            
        return self
    