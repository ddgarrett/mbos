"""
    Print Service
    
    Print messages sent via the input queue.       
    
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
        self.count    = 0
        self.print_log = self.get_parm("print_log",1)

    async def run(self):
        # print("run print")
        q = self.get_input_queue()
        
        while True:
            # if not q.empty():
            # wait for input
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
            # await uasyncio.sleep_ms(0)
                            

    
