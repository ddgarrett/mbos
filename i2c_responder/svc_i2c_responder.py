"""
    I2C Controller Service
    
    Sends and recieves messages from I2C Responders.
    
    Input queue contains any outgoing messages.
    
    Also polls the I2C connection to see if there are any
    messages. Any messages are placed in the output queue.
    
"""

from service import Service
import queue
import uasyncio
from xmit_message import XmitMsg
import gc

# not needed?
# from i2c_responder import I2CResponder

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        # place self.i2c in default parms so other
        # services can access stats
        defaults = self.svc_parms["defaults"]
        defaults["i2c_interface"] = self.get_i2c()

    async def run(self):
        q_in  = self.input_queue
        q_out = self.output_queue
        
        i2c_responder = self.get_i2c()
        i2c_q_in  = i2c_responder.q_in
        i2c_q_out = i2c_responder.q_out
        
        while True:
            
            # pass any input messages to i2c responder
            # after converting to string
            while not q_in.empty():
                xmit = await q_in.get()
                if not i2c_q_in.full():
                    await i2c_q_in.put(xmit.dumps())
                    

            # pass any messages received by the i2c responder
            # to my output queue, after unwrapping the message
            while not i2c_q_out.empty():
                msg = await i2c_q_out.get()
                if len(msg) > 0:
                    xmit = XmitMsg(msg=msg)
                    xmit.unwrapMsg()
                    await q_out.put(xmit)
            
            # gc.collect()
            await uasyncio.sleep_ms(0)
