"""
    LCD Service
    
    Processes items in the input queue
    translating them to various commands related to the LCD.
    
    V02 uses a different driver which has more capabilities.
    
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
# from lcd1602 import LCD
# from lcd_api import LcdApi
from service import Service
from machine import Pin
from machine import I2C
from pico_i2c_lcd import I2cLcd


import utf8_char
import xmit_lcd

import queue
import uasyncio

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        #self.lcd = LCD(pin_sda=20, pin_scl=21)
        #
        # use pico_i2c_lcd instead of LCD1602
        
        i2c_controller = 0
        i2c_sda_pin    = int(self.get_parm("i2c0_sda_pin","20"))
        i2c_scl_pin    = int(self.get_parm("i2c0_sda_pin","21"))
        i2c_freq       = int(self.get_parm("i2c0_freq", "400_000"))
        
        i2c_addr       = int(self.get_parm("i2c_addr", "0x27"))
        lcd_row_cnt    = int(self.get_parm("lcd_row_cnt", "2"))
        lcd_col_cnt    = int(self.get_parm("lcd_col_cnt", "16"))
        
        
        
        i2c = I2C(i2c_controller, sda=Pin(i2c_sda_pin),
                  scl=Pin(i2c_scl_pin), freq=i2c_freq)

        
        self.lcd = I2cLcd(i2c, i2c_addr, lcd_row_cnt, lcd_col_cnt)
        
        self.backlight_on   = True
        self.blink_task     = None
        self.blink_interval = 0
        
        # Add any custom characters
        # Any custom characters must have a byte array
        # defined in utf8_char.py in the dictionary CUSTOM_CHARACTERS
        custom_char = self.get_parm("custom_char","")
        for char in custom_char:
            if char in utf8_char.CUSTOM_CHARACTERS:
                b_array = utf8_char.CUSTOM_CHARACTERS[char]
                self.lcd.def_special_char(char,b_array)

        # dictionary to execute commands
        self.cmd_lookup = {
            xmit_lcd.CMD_CLEAR_SCREEN : self.lcd.clear,

            xmit_lcd.CMD_CURSOR_ON    : self.lcd.show_cursor,
            xmit_lcd.CMD_CURSOR_OFF   : self.lcd.hide_cursor,

            xmit_lcd.CMD_BLINK_CURSOR_ON  : self.lcd.blink_cursor_on,
            xmit_lcd.CMD_BLINK_CURSOR_OFF : self.lcd.blink_cursor_off,

            xmit_lcd.CMD_BACKLIGHT_ON  : self.lcd.backlight_on,
            xmit_lcd.CMD_BACKLIGHT_OFF : self.lcd.backlight_off,

            xmit_lcd.CMD_DISPLAY_ON  : self.lcd.display_on,
            xmit_lcd.CMD_DISPLAY_OFF : self.lcd.display_off
        }
        
    # run forever, but only blink backlight if
    # blink_interval > 0
    async def blink_lcd(self):
        while True:
            while self.blink_interval > 0:
                self.set_backlight(False)
                await uasyncio.sleep_ms(int(self.blink_interval * 1000))
                self.set_backlight(True)
                await uasyncio.sleep_ms(int(self.blink_interval * 1000))
                
            await uasyncio.sleep_ms(500)
        
    async def run(self):
        q = self.get_input_queue()
        
        # Start the blink coroutine.
        # It won't do anything until blink_interval is set
        self.blink_task = uasyncio.create_task(self.blink_lcd())
        
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
            if command in self.cmd_lookup:
                self.cmd_lookup[command]()
            else:
                # log error: invalid command?
                pass
        elif isinstance(command,dict):
            for key in command:
                if key == 'msg':
                    self.lcd.putstr(command[key])
                elif key == 'cursor':
                    self.set_cursor(command[key])
                elif key == 'backlight':
                    self.set_backlight(command[key])
                elif key == 'blink_backlight':
                    self.blink_interval = command[key]
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
                self.lcd.move_to(x,y)
                return
            
        # log error in cursor command?
                
    def set_backlight(self, value):
        if value:
            self.lcd.backlight_on()
            self.backlight_on = True
        else:
            self.lcd.backlight_off()
            self.backlight_on = False
            
                
        

    