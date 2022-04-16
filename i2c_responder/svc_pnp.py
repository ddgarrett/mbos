"""
    Plug and Play Service
    
    Receives two messages:
    - "ext_svc" repsond by sending to the "send from"
       a list of external services supported by this Responder.
       
    - "ext_menu" respond by sending a list of menu items for the external services on this
      responder to the "send from"
    
"""

from service import Service
import queue
import uasyncio
from xmit_message import XmitMsg


# All services classes are named ModuleService
class ModuleService(Service):

    async def run(self):
        q = self.get_input_queue()
        
        while True:
            xmit = await q.get()
            fr = xmit.get_from()
            msg = xmit.get_msg()
            
            # responder to sender of message (fr)
            # with either external services list
            # or external menu list
            if msg == "ext_svc":
                if "ext_svc" in self.svc_parms:
                    d = {"ext_svc" : self.svc_parms["ext_svc"],
                         "i2c_addr": self.get_parm("ic2_responder_addr",None)}
                    xmit = XmitMsg(self.name,fr, d)
                    await self.put_to_output_q(xmit)
                    
            elif msg == "ext_menu":
                if "ext_menu" in self.svc_parms:
                    d = {"ext_menu" : self.svc_parms["ext_menu"]}
                    xmit = XmitMsg(self.name,fr, d)
                    await self.put_to_output_q(xmit)                
            
                            

    

