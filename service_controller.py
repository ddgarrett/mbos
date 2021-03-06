"""
    Controller Service
    
    Special Service to Manage other Services.
    
    Tracks service that currently has focus.
    
    Sends other services messages to tell them to:
     - lose focus - should stop sending messages to the display or other output device
     - gain focus - begin sending messages to display or other output device
     
    Also has parameter to determine who initial focus should be.
    
    For now - may also implement a function menu to allow use to select an active app?
    Or may be in a separate menu service which receives focus like other services?
    
"""

from service import Service
from xmit_message import XmitMsg
from svc_i2c_stub import fwd_i2c_msg

import queue
import uasyncio
import gc
# import xmit_ir_remote

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.has_focus_svc = None
        self.focus_queue = []
        
        self.ir_remote = self.get_parm("ir_remote",None)
        self.svc_lookup = None

    # Check output queue for each service.
    # If there is an output queue record, pass it to the appropriate input queue.
    # svc_dict is a dictionary containing one entry for each service.
    # Key is the service name, as specified in the .json startup file.
    # Value is the service object.
    async def poll_output_queues(self, svc_lookup, log_xmit):
        
        # below used by self.run() to add external services
        self.svc_lookup = svc_lookup
        
        xmit_passed = False
        
        # check each service output queue to see if a message was sent
        # if it was, pass it to the input queue for the "to" service
        for svc in self.svc_lookup.values():
            q_svc_output = svc.get_output_queue()
            
            if not q_svc_output.empty():
                xmit = await q_svc_output.get()
                
                # pass message to queue for specified service
                to = xmit.get_to()
                fr = xmit.get_from()
                
                if to == "focus":
                    xmit.set_to(self.has_focus_svc)
                    to = self.has_focus_svc
                    
                if to in self.svc_lookup:
                    q_svc_input = self.svc_lookup [to].get_input_queue()

                    # avoid logging my sending a message to log
                    # if to != "log":
                    xmit_passed = True
                        
                    await q_svc_input.put(xmit)
                    
                    # should we log all messages passed from one service to another?
                    if log_xmit and xmit.to != "log":
                        await self.log_msg(xmit.dumps())
                        
                else:
                    if log_xmit:
                        await self.log_msg("ignore: " + xmit.dumps())

                # allow co-routines to execute
                # - not needed if we only process max one message per output queue
                # await uasyncio.sleep_ms(0)
                
            # allow co-routines to execute
            await uasyncio.sleep_ms(0)
            
        return xmit_passed
    
    
    async def run(self):
        
        focus_svc = self.get_parm("startup_focus","menu")
        
        await self.log_msg("sending gain focus to " + focus_svc)
        await self.send_gain_focus(focus_svc)
        self.has_focus_svc = focus_svc
        
        q_input = self.get_input_queue()
        
        while True:
            #if not q_input.empty():
            # wait until there is input
            xmit = await q_input.get()
            msg = xmit.get_msg()
            
            if isinstance(msg,str):
                fr = xmit.get_from()
                await self.process_msg(fr, msg)
            elif (isinstance(msg,dict) and
                  "ext_svc" in msg):
                await self.insert_ext_svc(msg)

            # give co-processes a chance to run
            await uasyncio.sleep_ms(0)
            
    async def insert_ext_svc(self, msg):
        
        svc_parm_list = msg["ext_svc"]
        i2c_addr = msg["i2c_addr"]
        
        # svc_lookup = self.svc_lookup
        defaults = self.svc_parms["defaults"]
        
        # import the modules for services
        for svc_parms in svc_parm_list:
            svc_parms["defaults"] = defaults  # every service has access to defaults
            module = __import__(svc_parms['module'])
            svc = module.ModuleService(svc_parms)
            self.svc_lookup[svc_parms['name']] = svc
            uasyncio.create_task(svc.run())
            
            await self.log_msg("started svc {} for responder {}".format(svc_parms['name'],i2c_addr))
        
        # clean up now?
        gc.collect()
        
        # Request sender to now send a list of any external menu items
        # to be added to the menu list. Have them send it to the "menu" service.
        xmit = XmitMsg(self.MENU_SVC_NAME, "pnp_svc", "ext_menu")
        xmit = fwd_i2c_msg(self.MENU_SVC_NAME, xmit, i2c_addr)
        # print(xmit)
        await self.get_output_queue().put(xmit)
        
    async def process_msg(self, fr, msg):
        if msg == self.CTL_PUSH_FOCUS_MSG:
            self.focus_queue.append(self.has_focus_svc)
            await self.send_lose_focus(self.has_focus_svc)
            await self.send_gain_focus(fr)
            self.has_focus_svc = fr
            
            return True
        
        if msg == self.CTL_XFER_FOCUS_MSG:
            await self.send_lose_focus(self.has_focus_svc)
            await self.send_gain_focus(fr)
            self.has_focus_svc = fr
            return True
        
        if msg == self.CTL_POP_FOCUS_MSG:
            if len(self.focus_queue) == 0:
                return False
            
            await self.send_lose_focus(self.has_focus_svc)
            self.has_focus_svc = self.focus_queue[-1]
            await self.send_gain_focus(self.has_focus_svc)
            del self.focus_queue[-1]
            return True
        
        # TODO: use the focus stack to pass events up the stack
        if fr == self.ir_remote:

            # If Menu is NOT the current focus svc
            # pass this message on to the Menu
            # Menu must NOT pass it back or else
            # we'll end up in an infinite loop
            if not self.has_focus_svc == 'menu':
                rexmit = XmitMsg(self.ir_remote,'menu',msg)
                await self.put_to_output_q(rexmit)
            
        return False
            
    async def send_gain_focus(self, service_name):
        await self.send_msg(service_name,self.CTL_GAIN_FOCUS_MSG)
        
    async def send_lose_focus(self, service_name):
        await self.send_msg(service_name,self.CTL_LOSE_FOCUS_MSG)
        
        
                            

    
