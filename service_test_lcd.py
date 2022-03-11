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

    def set_tests(self,xmit):
        return [ xmit.set_cursor_on, xmit.set_cursor_off,
                  xmit.set_blink_cursor_on, xmit.set_blink_cursor_off,
                  xmit.set_cursor_off,
                  xmit.set_backlight_off, xmit.set_backlight_on,
                  xmit.set_display_off, xmit.set_display_on
            ]
        
    async def run_test(self):
        while True:
            xmit = xmit_lcd.XmitLcd(fr=self.name)
            xmit.clear_screen().set_msg("⏶ press any key" + "\n⏷ to start tests")
            await self.put_to_output_q(xmit)
            
            tests = self.set_tests(xmit)
            
            await self.await_ir_input()
            
            for i in range(len(tests)):
                xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
                tests = self.set_tests(xmit)
                test_name = str(tests[i].__name__)
                xmit.set_msg(test_name+"\n")
                tests[i]()
                await self.put_to_output_q(xmit)
                
                # prevent up/down arrows from leaving display
                await self.await_ir_input(control_keys=None) 
            


