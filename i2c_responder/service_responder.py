"""
    Responder Service
    
    Polls in/out I2C lines.
    
    Input queue items are sent to the Controller
    when requested.
    
    Messages sent by the Controller are placed
    on the output queue.
    
    If Controller polls service and nothing is in
    the input queue, returns a message showing 0 length.
    
"""

from service import Service
import queue
import uasyncio

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.last_msg = None
        self.last_fr  = None
        self.rcv_cnt   = 0
        self.send_cnt  = 0
        self.print_log = self.get_parm("print_log",1)

    async def run(self):
        # print("run print")
        q = self.get_input_queue()
        
        while True:
            if not q.empty():
                xmit = await q.get()
                
                if self.print_log:
                    msg = xmit.get_msg()
                    fr = xmit.get_from()
                    if self.last_fr == fr and self.last_msg == msg:
                        if self.count == 0:
                            self.count = 1
                            print("... 1", end="")
                        else:
                            self.count = self.count+1
                            print(" " + str(self.count),end="" )
                    else:
                        if self.count != 0:
                            print(" ")  # print newline character
                            self.count = 0
                            
                        self.last_fr = fr
                        self.last_msg = msg
                        print(fr + ": " + msg)

            # give co-processes a chance to run
            await uasyncio.sleep_ms(0)
                            
                            
    """
        process_i2c_rcv waits for any messages
        sent by the controller and place them on the output
        queue for this service.
    """
    async def process_i2c_rcv(self):
        pass
    
    """
        process_i2c_send waits for the controller to
        poll for messages. If any messages are in the
        input queue for this service, it sends them to the
        controller.
        
        If no messages are in the input queue, this service
        responds with a zero length message (four bytes, all 0)
        to avoid hanging up the controller.
    """
    async def process_i2c_send(self):
        pass
    

