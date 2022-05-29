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
        self.send_to = self.get_parm("send_to","remote_log")
        self.send_cnt = 0
            
    async def gain_focus(self):
        await super().gain_focus()
        await self.init_display()
        
    async def init_display(self):
        controller = self.get_parm("i2c_interface",None)
        
        xmit = xmit_lcd.XmitLcd(fr=self.name).clear_screen()
        xmit.set_msg("⏶ press any key" + "\n⏷ to send 10 xmit\np:       {}".format(self.send_to))
        await self.put_to_output_q(xmit)

        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(2,2).set_msg(str(self.send_cnt))
        
        m = "s{} r{} x{} f{}".format(controller.send_cnt,
                controller.rcv_cnt, controller.resend_cnt, controller.failed_cnt )
            
        xmit.set_cursor(0,3).set_msg(m)
        await self.put_to_output_q(xmit)


    async def process_ir_input(self,xmit):
        
        controller = self.get_parm("i2c_interface",None)
        self.send_cnt += 1
        
        xmit = xmit_lcd.XmitLcd(fr=self.name).blk_hg()
        xmit.set_cursor(2,2).set_msg(str(self.send_cnt)) 
        await self.put_to_output_q(xmit)

        # send a quick burst of 10 messages
        for i in range(10):
            await self.send_msg(self.send_to,"test forwarded message!")
            await uasyncio.sleep_ms(500)

            m = "s{} r{} x{} f{}".format(controller.send_cnt,
                controller.rcv_cnt, controller.resend_cnt, controller.failed_cnt )

            xmit = xmit_lcd.XmitLcd(fr=self.name)         
            xmit.set_cursor(0,3).set_msg(m)
            await self.put_to_output_q(xmit)
        






                

            


