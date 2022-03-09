"""
    DHT11 Service
    
    Check DHT11 input every 2 seconds and
    send temperature and humidity to the LCD Service.
    
"""

from service import Service
import queue
import uasyncio

import xmit_lcd
import xmit_message_handler
# import xmit_ir_remote
import utf8_char

from dht11 import DHT11, InvalidChecksum
from machine import Pin

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.sensor = DHT11(Pin(16, Pin.OUT, Pin.PULL_DOWN))

    async def run(self):
        
        # add input queue handlers
        self.h = xmit_message_handler.XmitMsgHandler(2)
        self.h.add_handler(self.get_parm("ir_remote",None),self.handle_ir_key_xmit,True)
        self.h.add_handler(self.CTL_SERVICE_NAME,self.handle_controller_xmit,True)
        
        q_in  = self.get_input_queue()
        q_out = self.get_output_queue()
        
        while True:
            while not q_in.empty():
                xmit = await q_in.get()
                await self.h.process_xmit(xmit, q_out)
                
            if self.has_focus and self.display_on:
                await self.update_lcd()

                # Check DHT11 max is every two seconds
                await uasyncio.sleep_ms(2000)
                
            await uasyncio.sleep_ms(0)

    # handle key code xmit from IR input device
    async def handle_ir_key_xmit(self,xmit):
        if xmit.get_msg() == utf8_char.KEY_POWER_OFF:
            if not self.display_on:
                await self.init_lcd()
                self.display_on = True
            else:
                await self.turn_off_lcd()
                self.display_on = False
                
            return True

        return False
     
    async def handle_controller_xmit(self, xmit_msg):
        # Only expect lose or gain focus messages from controller
        if xmit_msg.get_msg() == self.CTL_GAIN_FOCUS_MSG:
            await self.init_lcd()
            self.has_focus = True
            self.display_on  = True
            return True
        
        if xmit_msg.get_msg() == self.CTL_LOSE_FOCUS_MSG:
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
        msg.clear_screen().set_msg("Temp:\nHumidity:")
        await self.put_to_output_q(msg)
        # await self.log_msg("Sent LCD Initialize Message")
        
    # update LCD temp/humidity values
    async def update_lcd(self):
        temp = 0
        humidity = 0
        update_ok = True
        
        try: 
            temp = self.sensor.temperature * 1.8 + 32
            humidity = self.sensor.humidity
        except Exception as e:
            update_ok = False
            await self.log_msg(e)
            #print(e)
        
        if update_ok:
            # adjustments based on comparison to commercial product
            temp = temp - 1.7
            humidity = humidity + 10
            
            msg = xmit_lcd.XmitLcd(fr=self.name)
            msg.set_cursor(6,0).set_msg("{: .1f} F".format(temp))
            msg.set_cursor(10,1).set_msg("{:.0f}%".format(humidity))
            
            await self.put_to_output_q(msg)
            
            # If update was okay, wait an additional 3 seconds (5 total) 
            # await uasyncio.sleep_ms(3000)



    

