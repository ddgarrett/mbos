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
            xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
            xmit.set_msg("⏶ press any key" + "\n⏷ to start tests")
            await self.put_to_output_q(xmit)
            
            tests_len = len(self.set_tests(xmit))
            lcd_col_cnt = self.get_parm("lcd_col_cnt",16)
            await self.await_ir_input()

            i = 0
            while i < tests_len:

                xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
                
                tests = self.set_tests(xmit)
                test_name = str(tests[i].__name__)
                prompt = "⏴ " + test_name+(" "*(lcd_col_cnt-2))
                
                # replace last character on display with "⏵"
                prompt = prompt[:lcd_col_cnt-2] + "⏵\n"
                
                xmit.set_msg(prompt)
                tests[i]() # actually execute the test
                
                await self.put_to_output_q(xmit)
                
                # prevent up/down arrows from leaving display: control_keys=None
                key = (await self.await_ir_input(control_keys=None)).get_msg()
                
                if key == "⏴":
                    i -= 1
                    if i < 0:
                        # exit inner loop if left arrow on first test
                        i = len(tests)
                else:
                    i += 1

                    
                 


                

            


