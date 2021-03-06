"""
    Run Neopixel LEDs
    
    Allow IR to control speed and pixel hue increment
    of flashing lights.
    
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
        
        self.incr = .05 # how much to increment between LED
        self.wait = 10  # wait in ms
        
        self.ws = WS2812(machine.Pin(0),8)
        
        self.incr_val = self.incr_wait
        
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
        for j in range(7, -1, -1):
            await uasyncio.sleep_ms(1)
            self.ws[j] = [r,g,b]
            self.ws.write()
            
    async def write_hsv(self):        
        
        h = 0.0
        incr = self.incr
        
        while True:
            if incr != self.incr:
                h = 0.0
                incr = self.incr
                
            h = h + incr
            while h < 0: 
                h = h + 1
            while h > 1:
                h = h - 1
                
            for j in range(8):
                hp = h + j * self.incr
                while hp > 1:
                    hp = hp - 1 # - self.incr
                while hp < 0:
                    hp = hp + 1
                    
                await uasyncio.sleep_ms(1)
                r,g,b = hsv_to_rgb.cnv(hp,self.s,self.v)
                self.ws[7-j] = [r,g,b]
                self.ws.write()
                
            await uasyncio.sleep_ms(self.wait)
        
    # Update display
    async def display_iwv(self):
        xmit = xmit_lcd.XmitLcd(fr=self.name).blk_hg() # blank out hourglass
        dat = self.fmt_dsp_dat()
        for i in range(len(dat)):
            xmit.set_cursor(14,i).set_msg("{}  ".format(dat[i]))
        await self.put_to_output_q(xmit)
        
    # Initialize the LCD display
    async def init_display(self):
        xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
        dat = self.fmt_dsp_dat()
        xmit.set_msg("??? incr(ok,a): {} \n??? wait(*)   : {} \n  value(#)  : {} \n  buff      : {}".
                     format(*dat))
        await self.put_to_output_q(xmit)
        
    # calculate display values
    def fmt_dsp_dat(self):
        incr = int(round(self.incr*100,0))
        wait = self.wait
        hv = int(round(self.v*100,0))
        return [incr,wait,hv,self.buff]
        
    # increment/decrent increment, wait or v
    def incr_incr(self,incr):
        # print("increment h {}".format(incr))
        self.incr = self.incr + incr*.05
        
    def incr_wait(self,incr):
        self.wait = self.wait + incr*10
        
    def incr_v(self,incr):
        self.v = self.v + incr*.05

    # perform action after IR input 
    async def process_ir_input(self,xmit):
        
        msg = xmit.get_msg()
        
        update_led = True
        
        if msg == utf8_char.KEY_REVERSE_BACK:        # decrement last set var
            # print("reverse back")
            self.incr_val(-1)
            self.buff = ""
            
        elif msg == utf8_char.KEY_FORWARD_NEXT_PLAY: # increment last set var
            self.incr_val(1)
            self.buff = ""
            
        elif msg == utf8_char.KEY_OK:  # set increment
            self.incr_val = self.incr_incr
            if len(self.buff) >= 1:
                self.incr = float(self.buff)/100
                self.buff = ""
            else:
                self.incr = self.incr + 0.05
                
        elif msg == "*":               # set wait time
            self.incr_val = self.incr_wait
            
            if len(self.buff) >= 1:  
                self.wait = int(self.buff) 
                self.buff = ""
            else:
                self.wait= self.wait + 10
                
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
            
        await self.display_iwv()

        
        






                

            


