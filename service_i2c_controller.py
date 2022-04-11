"""
    I2C Controller Service
    
    Sends and recieves messages from I2C Responders.
    
    Input queue contains any outgoing messages. The original xmit
    containing to/from and message, must be "wrapped".
    See xmit_message.XmitMsg wrapXmit() and unwrapMsg().
    
    The message in the wrapped xmit is further enhanced by the I2C stub
    forwarding the xmit, to contain the I2C address to which the message will be sent.
    This service then forwards the wrapped message to the I2C address.
    
    Also polls the I2C responders to see if they have any input.
    Note that ALL responders must respond, if nothing else with a
    zero length message, or else this core will hang. (NOTE: maybe run
    this on a separate core?). Any responder messages are unwrapped and
    placed on the output queue. The unwrapped message will specify the
    from, to and message contents.
    
"""

from service import Service
import queue
import uasyncio
from xmit_message import XmitMsg
from i2c_controller import I2cController

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        # scl = self.get_parm("i2c_scl_pin",1)
        # sda = self.get_parm("i2c_sda_pin",0)
        # self.controller = I2cController(scl_pin=scl, sda_pin=sda )
        
        i2c = self.get_i2c()
        self.controller = I2cController(i2c=i2c )
        
        # self.controller = self.get_i2c()
        
        # responder addresses
        """
        addr = self.get_parm("resp_addr",[])
        self.resp_addr = []
        for a in addr:
            self.resp_addr.append(int(a))
        """
            
        # await self.log_msg("i2c polling: "+str(self.resp_addr))
        
        # place self.controller in default parms so other
        # services can access stats
        defaults = self.svc_parms["defaults"]
        defaults["i2c_interface"] = self.controller
        
        

    async def run(self):
        q_in  = self.input_queue
        q_out = self.output_queue
                
        ignore_addr = self.get_parm("ignore_addr",[])
        
        # get active i2c addresses
        poll_addr = self.controller.scan()
        for a in ignore_addr:
            a = int(a)
            if a in poll_addr:
                poll_addr.remove(a)
        
        # print("polling addresses: " + str(poll_addr))
        
        await self.log_msg("polling addresses: " + str(poll_addr))
        
        while True:
            
            # send any queued xmit
            while not q_in.empty():
                xmit = await q_in.get()
                wrapped_msg = xmit.get_msg()
                 
                # try to avoid hangups by send message to non-active bus address
                i2c_addr = wrapped_msg[0]
                msg = wrapped_msg[1]
                
                if i2c_addr in poll_addr:
                    await self.controller.send_msg(i2c_addr,msg)
                    # await self.log_msg("ctl sent: " + msg + " to " + str(i2c_addr))
                else:
                    await self.log_msg("skipped msg: " + msg)
                
                await uasyncio.sleep_ms(0)
                
            # poll i2c bus for any input
            for addr in poll_addr:
                msg = await self.controller.rcv_msg(addr)
                
                while len(msg) > 0:
                    # unwrap the message and place on output queue
                    xmit = XmitMsg(msg=msg)
                    xmit.unwrapMsg()
                    await q_out.put(xmit)
                    msg = await self.controller.rcv_msg(addr)
                    
                    await uasyncio.sleep_ms(0)
                    
                await uasyncio.sleep_ms(0)
                
            # wait 1/3 second before polling I2C bus again
            # TODO: base wait on number of ticks since last wait?
            #  - wait for at least 333 ticks since last polling
            await uasyncio.sleep_ms(333)
                            

    
