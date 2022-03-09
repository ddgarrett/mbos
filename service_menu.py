"""
    Menu Service
    
    Displays a menu of available Services
    allowing user to select one to run.
    
    Can also run in the background processing keys
    from IR Remote to select a Service or scroll up/down
    the list of availabe Services.
    
    Controller can pass keys to Menu while it's in the background???
    
"""

from service import Service
import queue
import uasyncio


from xmit_message import XmitMsg
import xmit_message
import xmit_lcd
import xmit_message_handler
# import xmit_ir_remote
import utf8_char


# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        # List of services
        self.menu = self.get_parm("menu",["menu"])
        self.current_svc = 0
        
        self.has_focus = False
        self.display_on = True
        
        self.initial_focus = True
        
        self.ir_remote = self.get_parm("ir_remote",None)
        
    async def run(self):
        
        # add input xmit queue handlers
        self.h = xmit_message_handler.XmitMsgHandler(2)
        self.h.add_handler(self.ir_remote,self.handle_ir_key_xmit,True)
        self.h.add_handler(self.CTL_SERVICE_NAME,self.handle_controller_xmit,True)
        
        q_in  = self.get_input_queue()
        q_out = self.get_output_queue()
        
        while True:
            while not q_in.empty():
                xmit = await q_in.get()
                await self.h.process_xmit(xmit, q_out)
                
            await uasyncio.sleep_ms(0)

    # handle key code xmit from IR input device
    async def handle_ir_key_xmit(self,xmit):
        """
        if xmit.get_msg() == utf8_char.KEY_POWER_OFF:
            if not self.display_on:
                await self.init_lcd()
                self.display_on = True
            else:
                await self.turn_off_lcd()
                self.display_on = False
                
            return True
        """
        
        ##### menu actions go here
        """
        if xmit.get_msg() == utf8_char.KEY_PLAY_PAUSE_TOGGLE \
           and self.has_focus:
            self.display_on = True
            await self.display_menu()
            return True
        """
        
        if xmit.get_msg() == utf8_char.KEY_INCREASE:
            self.current_svc = self.current_svc + 1
            if self.current_svc >= len(self.menu):
                self.current_svc = 0
            
            next_svc_name = self.menu[self.current_svc]
            
            # send a transfer focus message to the controller
            # as if it were from the next service
            xmit = XmitMsg(next_svc_name,self.CTL_SERVICE_NAME,self.CTL_XFER_FOCUS_MSG)
            await self.put_to_output_q(xmit)
            
            return True
        
        if xmit.get_msg() == utf8_char.KEY_DECREASE:
            self.current_svc = self.current_svc - 1
            if self.current_svc < 0:
                self.current_svc = len(self.menu) - 1
            
            next_svc_name = self.menu[self.current_svc]
            
            # send a transfer focus message to the controller
            # as if it were from the next service
            xmit = XmitMsg(next_svc_name,self.CTL_SERVICE_NAME,self.CTL_XFER_FOCUS_MSG)
            await self.put_to_output_q(xmit)
            
            return True
        
        # We NEVER pass an ir remote message back to the controller
        # IF we do, an infinite loop will result
        return True
    
    # display the services menu
    async def display_menu(self):            
        await self.update_lcd("press up or down\n arrows")
                
    async def handle_controller_xmit(self, xmit_msg):
        # Only expect lose or gain focus messages from controller
        if xmit_msg.get_msg() == self.CTL_GAIN_FOCUS_MSG:
            if self.initial_focus:
                self.initial_focus = False
                initial_app = self.get_parm("initial_app","menu")
                if initial_app != "menu":
                    self.current_svc = self.get_parm("menu",None).index(initial_app)
                    xmit = XmitMsg(initial_app,self.CTL_SERVICE_NAME,self.CTL_PUSH_FOCUS_MSG)
                    await self.put_to_output_q(xmit)
                    return True
                
            await self.init_lcd()
            self.has_focus = True
            self.display_on  = True
            return True
        elif xmit_msg.get_msg() == self.CTL_LOSE_FOCUS_MSG:
            self.has_focus = False
            return True
            
        return False

    async def turn_off_lcd(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.set_backlight(0)
        await self.put_to_output_q(msg)
        
    # set LCD temp/humidity labels
    async def init_lcd(self):
        msg = "Select Function\nUp or Down arrow"
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.clear_screen().set_msg(msg)
        await self.put_to_output_q(xmit)
        
    # update LCD with msg
    async def update_lcd(self,msg):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.clear_screen().set_msg(msg)
        await self.put_to_output_q(xmit)


    

