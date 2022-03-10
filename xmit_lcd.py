"""
    Transmitted LCD Message class.
    
    Aids builing a message that is sent to service_lcd.
    LCD Commands are added to the message as invoked including:
    - clear_screen()    - clears the screen
    - set_cursor(x,y)   - sets cursor to specified x,y co-ordinates
    - set_msg(text)     - displays message text at current cursor position
    - set_backlight(on) - turns off backlight if on=0, otherwise sets backlight on
"""

from xmit_message import XmitMsg

class XmitLcd(XmitMsg):
    
    def __init__(self,fr="",to="lcd",msg=""):
        
        super().__init__(fr,to,msg)
        
        if self.msg == "":
            self.msg = []
        
    def set_msg(self,message):
        self.msg.append({"msg":message})
        return self
        
    def clear_screen(self):
        self.msg.append('clear')
        return self
        
    def set_cursor(self,x,y):
        if (type(x) is int) and (type(y) is int):
            self.msg.append({'cursor':[x,y]})
        else:
            # consider logging error?
            pass
        
        return self
        
    def set_backlight(self,on):
        if ((type(on) is int) and on == 0):
            self.msg.append({'backlight':0})
        else:
            self.msg.append({'backlight':1})
            
        return self
    
    def blink_backlight(self,interval):
        x = interval * 1000  # cause exception if we can't multiply interval by 1,000
        self.msg.append({'blink_backlight':interval})
            
        
