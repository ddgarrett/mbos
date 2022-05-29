"""
    Buzzer Service
    
    Produce buzz sound using active buzzer.
    
"""

from service import Service
import queue
import uasyncio
from machine import Pin

            
# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.buzzer = Pin(15, Pin.OUT)

    async def run(self):
        q = self.get_input_queue()
        
        while True:
            xmit = await q.get()
            
            if self.get_parm("sound_on",True):
                await self.buzz(100)
            

    async def buzz(self,sleep_ms):
        self.buzzer.toggle()
        await uasyncio.sleep_ms(sleep_ms)
        self.buzzer.toggle()
        await uasyncio.sleep_ms(sleep_ms)

        
        

