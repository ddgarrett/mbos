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
import utime

from dht11 import DHT11, InvalidChecksum
from machine import Pin

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.sensor = DHT11(Pin(16, Pin.OUT, Pin.PULL_DOWN))
        self.display_task = None

    async def gain_focus(self):
        await super().gain_focus()
        await self.init_lcd()
        
        if self.display_task == None:
            self.display_task = uasyncio.create_task(self.display_data())
        else:
            self.log_msg("*** ERROR: display_task already running?")

    async def lose_focus(self):
        if self.display_task != None:
            self.display_task.cancel()
            self.display_task = None
        
        await super().lose_focus()
        
        
    # set LCD temp/humidity labels
    async def init_lcd(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen().set_msg("⏶ Temp:\n⏷ Humidity:")
        await self.put_to_output_q(msg)

    # asynchronous task to update data on LCD
    async def display_data(self):
        ticks_last_update = 0
        
        while True:
            # Check DHT11 max every two seconds
            ticks_now = utime.ticks_ms()
            if (ticks_now - ticks_last_update) > 2000:
                ticks_last_update = ticks_now
                await self.update_lcd()
                
            await uasyncio.sleep_ms(250)            

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
        
        if update_ok:
            # adjustments based on comparison to commercial product
            temp = temp - 1.7
            humidity = humidity + 10
            
            msg = xmit_lcd.XmitLcd(fr=self.name)
            msg.set_cursor(8,0).set_msg("{: .1f}°F".format(temp))
            msg.set_cursor(12,1).set_msg("{:.0f}%".format(humidity))
            
            await self.put_to_output_q(msg)



    

