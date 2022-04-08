"""
    Test Harness Service
    
"""


from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.send_cnt = 0
            
    async def gain_focus(self):
        await super().gain_focus()
        await self.run_test()

    async def run_test(self):
        
        xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
        xmit.set_msg("⏶ press any key" + "\n⏷ to start tests\n    sent: ")
        await self.put_to_output_q(xmit)

        
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(10,2).set_msg(str(self.send_cnt))
        await self.put_to_output_q(xmit)
        
        while True:


            # print("************************** svc_test_i2c: awaiting IR input")
            await self.await_ir_input()
            
            self.send_cnt += 1
                        
            xmit = xmit_lcd.XmitLcd(fr=self.name)
            xmit.set_cursor(10,2).set_msg(str(self.send_cnt))
            await self.put_to_output_q(xmit)

            # send a quick burst of 10 messages
            # print("************************** svc_test_i2c: ")
            for i in range(10):
                await self.send_msg("remote_log","test forwarded message!")
                await uasyncio.sleep_ms(333)

            await uasyncio.sleep_ms(0)






                

            


