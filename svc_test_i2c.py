"""
    Test Harness Service
    
"""


from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

# All services classes are named ModuleService
class ModuleService(Service):

    async def gain_focus(self):
        await super().gain_focus()
        await self.run_test()

    async def run_test(self):
        
        while True:
            xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
            xmit.set_msg("⏶ press any key" + "\n⏷ to start tests")
            
            await self.put_to_output_q(xmit)
            
            await self.await_ir_input()

            await self.send_msg("remote_log","test forwarded message!")






                

            


