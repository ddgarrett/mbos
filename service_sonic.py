"""
    Sonic Distance Finder Service
    
    Check distance via sonic reflection every 2 seconds.
    Send distance to the LCD Service.
    
    Determines distance based on how long a sonic wave
    takes to go to and from an object.
    
"""

from service import Service
import queue
import uasyncio

import xmit_lcd
import xmit_message_handler
# import xmit_ir_remote

from machine import Pin
import utime

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.trigger = Pin(15, Pin.OUT)
        self.echo = Pin(14, Pin.IN)
        
        self.ir_remote = self.get_parm("ir_remote",None)
        
    async def run(self):
        
        # add input queue handlers
        self.h = xmit_message_handler.XmitMsgHandler(2)
        self.h.add_handler(self.ir_remote,self.handle_ir_key_xmit,True)
        self.h.add_handler(self.CTL_SERVICE_NAME,self.handle_controller_xmit,True)
        
        q_in  = self.get_input_queue()
        q_out = self.get_output_queue()
        
        while True:
            # while not q_in.empty():
            xmit = await q_in.get()
            await self.h.process_xmit(xmit, q_out)
                
            # await uasyncio.sleep_ms(0)

    # handle key code xmit from IR input device

    async def handle_ir_key_xmit(self,xmit):
        
        """
        if xmit.get_msg() == xmit_ir_remote.POWER_BUTTON:
            if not self.display_on:
                await self.init_lcd()
                self.display_on = True
            else:
                await self.turn_off_lcd()
                self.display_on = False
                
            return True
        
        # take a distance measurement
        if xmit.get_msg() == xmit_ir_remote.RUN_PAUSE_BUTTON:
            self.display_on = True
            await self.display_distance()
            return True
            
        """
        
        
        return False
    
    # display the distance based on sonic echo
    async def display_distance(self):
        distance = self.measure_distance()
        
        if distance > 18 :
            distance = distance/12
            distance = "{:.2f} ft".format(distance)
        else:
            distance = "{:.2f} inches".format(distance)
            
        await self.update_lcd(distance)
        
        
    # Returns distance in inches based on how long a sound
    # took to return an echo.
    # NOTE: does a non-async sleep but it's only
    # on the order of microseconds
    def measure_distance(self):
        # make sure the trigger is low
        self.trigger.low()
        utime.sleep_us(2)
        
        # set trigger high for 5 micro seconds
        self.trigger.high()
        utime.sleep_us(5)
        self.trigger.low()
        
        # wait for echo to go high
        while self.echo.value() == 0:
            signaloff = utime.ticks_us()
        
        # count how long it remains high
        while self.echo.value() == 1:
            signalon = utime.ticks_us()
            
        # how far the sound traveled to and from object
        # based on how far it went in 5 microseconds
        timepassed = signalon - signaloff
        distance = (timepassed * 0.0343) / 2
        distance = distance * 0.393701  # convert to inches
        
        return distance
        
        
    async def handle_controller_xmit(self, xmit_msg):
        # Only expect lose or gain focus messages from controller
        if xmit_msg.get_msg() == self.CTL_GAIN_FOCUS_MSG:
            await self.init_lcd()
            self.has_focus = True
            self.display_on  = True
            return True
        elif xmit_msg.get_msg() == self.CTL_LOSE_FOCUS_MSG:
            self.has_focus = False
            return True
            
        return False

    async def turn_off_lcd(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.set_backlight(0)
        await self.put_to_output_q(msg)
        
    # set LCD temp/humidity labels
    async def init_lcd(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen().set_msg("Press Play/Pause button\nto measure dist.")
        await self.put_to_output_q(msg)
        
    # update LCD with distance value
    async def update_lcd(self,distance):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen().set_msg(distance)
        await self.put_to_output_q(msg)


    

