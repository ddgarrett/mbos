"""
    Run Neopixel LEDs
    
"""


from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

import machine
# import utime
import math
from ws2812 import WS2812
import hsv_to_rgb
import utf8_char

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.h = 0.0
        self.s = 1.0
        self.v = 0.5
        
        self.ws = WS2812(machine.Pin(0),8)
        
        self.incr_val = self.incr_h
        
        self.buff = ""
        
        self.run_neo_task = None
            
    async def gain_focus(self):
        await super().gain_focus()
        await self.init_display()
        self.run_neo_task = uasyncio.create_task(self.write_hsv())
        
        
    async def lose_focus(self):
        self.run_neo_task.cancel()
        self.run_neo_task = None
        await self.write_rgb(0,0,0)
        await super().lose_focus()
        
    async def write_rgb(self,r,g,b):
        for j in range(8):
            await uasyncio.sleep_ms(1)
            self.ws[j] = [r,g,b]
            self.ws.write()
            
    async def write_hsv(self):
        if self.h > 1:
            self.h = 0
        if self.s > 1:
            self.s = 0
        if self.v > 1:
            self.v = 0
            
        if self.h < 0:
            self.h = 1
        if self.s < 0:
            self.s = 1
        if self.v < 0:
            self.v = 1
            
        # r,g,b = hsv_to_rgb.cnv(self.h,self.s,self.v)

        # print(self.h,self.s,self.v)
        # print(r,g,b)
        # await self.write_rgb(r,g,b)
        
        
        h = self.h
        
        while True:
            h = h + .05
            if h < 0: # (self.h + 8*.05):
                h = 1
                
            for j in range(8):
                hp = h + j * .05
                while hp > 1:
                    hp = hp - 1.05
                    
                await uasyncio.sleep_ms(1)
                r,g,b = hsv_to_rgb.cnv(hp,self.s,self.v)
                self.ws[7-j] = [r,g,b]
                self.ws.write()
                
            await uasyncio.sleep_ms(10)
        
    async def display_hsv(self):
        hp = int(round(self.h*100,0))
        hs = int(round(self.s*100,0))
        hv = int(round(self.v*100,0))
        xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
        xmit.set_msg("⏶ h:{} s:{} v:{} \n⏷ {}".format(hp,hs,hv,self.buff))
        await self.put_to_output_q(xmit)
        
    # Initialize the LCD display
    async def init_display(self):
        await self.display_hsv()
        # await self.write_hsv()
        
    # increment/decrent h,s or v
    def incr_h(self,incr):
        print("increment h {}".format(incr))
        self.h = self.h + incr
        
    def incr_s(self,incr):
        self.s = self.s + incr
        
    def incr_v(self,incr):
        self.v = self.v + incr

    # perform action after IR input 
    async def process_ir_input(self,xmit):
        
        msg = xmit.get_msg()
        
        update_led = True
        
        if msg == utf8_char.KEY_REVERSE_BACK:        # decrement last set var
            print("reverse back")
            self.incr_val(-0.05)
            self.buff = ""
            
        elif msg == utf8_char.KEY_FORWARD_NEXT_PLAY: # increment last set var
            self.incr_val(0.05)
            self.buff = ""
            
        elif msg == utf8_char.KEY_OK:  # set h
            self.incr_val = self.incr_h
            if len(self.buff) >= 1:
                self.h = float(self.buff) / 100.0
                self.buff = ""
            else:
                self.h = self.h + 0.05
                
        elif msg == "*":               # set s
            self.incr_val = self.incr_s
            
            if len(self.buff) >= 1:  
                self.s = float(self.buff) / 100.0
                self.buff = ""
            else:
                self.s = self.s + 0.05
                
        elif msg == "#":               # set v
            self.incr_val = self.incr_v
            
            if len(self.buff) >= 1:
                self.v = float(self.buff) / 100.0
                self.buff = ""
            else:
                self.v = self.v + 0.05
                
        else:                          # buffer any digits
            update_led = False
            if msg >= "0" and msg <= "9":
                self.buff = self.buff + msg
                
        # if update_led:
        #     await self.write_hsv()
        
        if self.h > 1:
            self.h = 0
        if self.s > 1:
            self.s = 0
        if self.v > 1:
            self.v = 0
            
        if self.h < 0:
            self.h = 1
        if self.s < 0:
            self.s = 1
        if self.v < 0:
            self.v = 1
            
        await self.display_hsv()

        
        






                

            


