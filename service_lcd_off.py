"""
    LCD Off Service
    
    When gains focus, turn off LCD
    
"""

from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

# All services classes are named ModuleService
class ModuleService(Service):

    async def gain_focus(self):
        await super().gain_focus()
        await self.turn_off_lcd()
        
    async def turn_off_lcd(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen()
        msg.set_backlight(0)
        await self.put_to_output_q(msg)
        



    

