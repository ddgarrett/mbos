"""
    I2C Stub Service
    
    Used when a service actually exists on another I2C node as
    either a Controller or Responder.
    
    Any input queue records are "wrapped" in an xmit which
    is sent to the "i2c_svc" input queue. IF the parms specify a
    "forward_i2c_addr" parm, the message in the xmit is further wrapped to be
    inside a dictionary under the name "msg". An additional field, "i2c_addr",
    is then added to the dictionary and the dictionary is stored in the
    xmit message field.
    
    NOTE: may have problems with focus events? And possibly control key events?
    
"""

from service import Service
import queue
import uasyncio

# Create an xmit which will forward an xmit
# to a given i2c_addr. 
def fwd_i2c_msg(fr,xmit,i2c_addr):
    xmit = xmit.wrapXmit(fr=fr, to="i2c_svc")
    msg = xmit.get_msg()
    new_msg = [i2c_addr, msg]
    xmit.msg = new_msg
    return xmit

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.i2c_addr = self.get_parm("forward_i2c_addr",None)
        
        if self.i2c_addr != None:
            self.i2c_addr = int(self.i2c_addr)

    async def run(self):
        # print("run print")
        q_in  = self.input_queue
        q_out = self.output_queue
        
        while True:
            # if not q_in.empty():
            xmit = await q_in.get()
            
            # await self.log_msg("stub fwd: " + xmit.dumps())
            
            """
            xmit = xmit.wrapXmit(fr=self.name, to="i2c_svc")
            msg = xmit.get_msg()
            new_msg = [self.i2c_addr, msg]
            xmit.msg = new_msg
            """
            xmit = fwd_i2c_msg(self.name,xmit,self.i2c_addr)
            
            await q_out.put(xmit)
                
            # give co-processes a chance to run
            # await uasyncio.sleep_ms(0)
                            

    
