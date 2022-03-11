"""
    LCD Service
    
    Processes items in the input queue
    translating them to various commands related to the LCD.
    
    See xmit_lcd.py for how to build input messages for this service.
    
    Accepts following commands:
        'clear'               clears LCD display
        {'cursor':[x,y]}      sets cursor to x (column 0 thru ??), y (row = 0 or 1)
        {'backlight':1}       turns backlight on (1) or off (0)
        {'msg':'some text'}   displays 'some text'
    
    Examples:
    
       ['clear',{'msg':'Temp:'},{'cursor':[0,1]},{'msg':'Humidity:'}]
       
       [{'cursor':[6,0]},{'msg':' 69.9'},{'cursor':[10,1]},{'msg':'38'}]
       
       
    
"""
from lcd1602 import LCD
# from lcd_api import LcdApi
from service import Service

import queue
import uasyncio

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.lcd = LCD(pin_sda=20, pin_scl=21)
        self.lcd_on = 1

    async def run(self):
        q = self.get_input_queue()
        
        while True:
            if not q.empty():
                msg = await q.get()
                self.process_msg(msg)

            # give co-processes a chance to run
            await uasyncio.sleep_ms(1)
                    
    def process_msg(self, xmit_msg):
            
        xmit_from = xmit_msg.get_from()
        xmit_to = xmit_msg.get_to()
        xmit_msg = xmit_msg.get_msg()
        
        if isinstance(xmit_msg,list):
            for command in xmit_msg:
                self.process_command(command)
        else:
            self.process_command(xmit_msg)
            
    def process_command(self, command):
        if isinstance(command,str):
            if command == 'clear':
                self.lcd.clear()
            else:
                # log error: invalid command?
                pass
        elif isinstance(command,dict):
            for key in command:
                if key == 'msg':
                    self.lcd.message(command[key])
                elif key == 'cursor':
                    self.set_cursor(command[key])
                elif key == 'backlight':
                    self.set_backlight(command[key])
                else:
                    # log error in dictionary command
                    pass
        else:
            # log error in command type?
            pass
        
    def set_cursor(self, xy):
        if isinstance(xy,list) and len(xy) == 2:
            x = xy[0]
            y = xy[1]
            
            if isinstance(x,int) and isinstance(y,int):
                self.lcd.set_cursor(x,y)
                return
            
        # log error in cursor command?
                
    def set_backlight(self, value):
        if isinstance(value,int):
            if value == 0:
                self.lcd.closelight()
                self.lcd_on = 0
            else:
                self.lcd.openlight()
                self.lcd_on = 1
                
            return
        
        # log error in backlight command?
                
        

    
