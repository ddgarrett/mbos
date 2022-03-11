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

CMD_CLEAR_SCREEN = 'clear'

CMD_CURSOR_ON    = 'cursor_on'
CMD_CURSOR_OFF   = 'cursor_off'

CMD_BLINK_CURSOR_ON  = 'blink_cursor_on'
CMD_BLINK_CURSOR_OFF = 'blink_cursor_off'

CMD_BACKLIGHT_ON  = 'backlight_on'
CMD_BACKLIGHT_OFF = 'backlight_off'

CMD_DISPLAY_ON  = 'display_on'
CMD_DISPLAY_OFF = 'display_off'



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
            self.set_backlight_off()
        else:
            self.set_backlight_on()
            
        return self
    
    def set_backlight_on(self):
        self.msg.append(CMD_BACKLIGHT_ON)
        return self
    
    def set_backlight_off(self):
        self.msg.append(CMD_BACKLIGHT_OFF)
        return self
    
    def set_cursor_on(self):
        self.msg.append(CMD_CURSOR_ON)
        return self
    
    def set_cursor_off(self):
        self.msg.append(CMD_CURSOR_OFF)
        return self
    
    def set_blink_cursor_on(self):
        self.msg.append(CMD_BLINK_CURSOR_ON)
        return self
        
    def set_blink_cursor_off(self):
        self.msg.append(CMD_BLINK_CURSOR_OFF)
        return self
        
    def set_display_on(self):
        self.msg.append(CMD_DISPLAY_ON)
        return self
        
    def set_display_off(self):
        self.msg.append(CMD_DISPLAY_OFF)
        return self
        
    
    # blink backlight at given rate
    # set interval to 0 to stop blinking
    def blink_backlight(self,interval):
        x = interval * 1000  # cause exception if we can't multiply interval by 1,000
        self.msg.append({'blink_backlight':interval})
            
        
