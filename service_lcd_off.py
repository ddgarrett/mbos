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
        await self.set_lcd_backlight(0)
        
    async def set_lcd_backlight(self, value):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen()
        msg.set_backlight(value)
        await self.put_to_output_q(msg)
        
        
    async def lose_focus(self):
        await self.set_lcd_backlight(1)
        await super().lose_focus()



    

