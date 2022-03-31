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

# not needed?
# from i2c_responder import I2CResponder

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)     

    async def run(self):
        q_in  = self.input_queue
        q_out = self.output_queue
        i2c_responder = self.get_i2c()
                
        while True:
            
            # is controller waiting for us to send data?
            while i2c_responder.read_is_pending():
                if not q_in.empty():
                    
                    xmit = await q_in.get()
                    print("i2c_svc input q: " + xmit.dumps())
                    # await i2c_responder.send_msg(xmit)
                    await i2c_responder.send_msg("")
                else:
                    await i2c_responder.send_msg("")

                
            # is controller trying to send us some data?
            while i2c_responder.write_data_is_available():
                msg = await i2c_responder.rcv_msg()
                
                if len(msg) > 0:
                    xmit = XmitMsg(msg=msg)
                    xmit.unwrapMsg()
                    await q_out.put(xmit)
    
                """
                print("rcv msg (",end="")
                print(len(msg),end="")
                print("): " + msg )
                """
                
            
            await uasyncio.sleep_ms(0)
                            

    

