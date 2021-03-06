"""
    Responder Service
    
    Replaces the Controller (service_controller.py module) used on the I2C Controller.
    
    Also see svc_i2c_responder.py which deals with sending/receiving I2C messages.
    
    This module:
    1. Polls all service output queues, passing output messages to the specified input queue.
       If a service with an input message does not exist, assume it is a remote service
       and pass the message to the I2C service
       
    2. Polls the controller input queue
"""

from service import Service
from xmit_message import XmitMsg
import queue
import uasyncio

# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.i2c_svc = self.get_parm("i2c_svc","i2c_svc")
        
    #
    # Check output queue for each service.
    # If there is an output queue record, pass it to the appropriate input queue.
    # svc_dict is a dictionary containing one entry for each service.
    # Key is the service name, as specified in the .json startup file.
    # Value is the service object.
    #
    # IF the service is not found, assume it is a remote service and placed in the
    # input queue for the i2c_svc service.
    #
    # Any messages sent to "controller" (this service) are also placed in the i2c_svc input queue
    # and then forwarded to the remote controller.
    #
    async def poll_output_queues(self, svc_lookup, log_xmit):
        
        xmit_passed = False
        
        i2c_q_in = svc_lookup[self.i2c_svc ].get_input_queue()
        
        # check each service output queue to see if a message was sent
        # if it was, pass it to the input queue for the "to" service
        for svc in svc_lookup.values():
            q_svc_output = svc.get_output_queue()
            if not q_svc_output.empty():
                xmit = await q_svc_output.get()
                # print(xmit.dumps())
                
                # pass message to queue for specified service
                to = xmit.get_to()
                fr = xmit.get_from()
                                    
                # forward message to i2c service to forward to remote Controller
                if (to == "controller") or not (to in svc_lookup):
                    await i2c_q_in.put(xmit)
                    
                    if log_xmit:
                        await self.log_msg(xmit.dumps())
                else:
                    q_svc_input = svc_lookup[to].get_input_queue()

                    # avoid logging my sending a message to log
                    if to != self.log_svc:
                        xmit_passed = True
                        
                    await q_svc_input.put(xmit)
                    
                    # should we log all messages passed from one service to another?
                    if log_xmit and xmit.to != self.log_svc:
                        await self.log_msg(xmit.dumps())

                # allow co-routines to execute
                # - not needed if we only process max one message per output queue
                # await uasyncio.sleep_ms(0)
                
            # allow co-routines to execute
            await uasyncio.sleep_ms(0)
            
        return xmit_passed
    
    # This run passes any services and menu items that need to be added
    # to the main Controller and Menu services.
    
    
    # After that run() method does not do anything.
    # Input queue messages sent to the controller are intercepted by the
    # poll_output_queue() method and passed directly to the i2c_svc.
    # Does check the input queue every few seconds just in case

    async def run(self):
        
        q_input = self.get_input_queue()
        
        # wait a few seconds to give Controller time to start up
        # no need to wait? is just placed on q out
        # await uasyncio.sleep_ms(3000)
        
        # send list of services to add to Controller services dictionary
        if "external_services" in self.svc_parms:
            d = {"ext_svc" : self.svc_parms["ext_svc"]}
            xmit = XmitMsg(self.name,self.CTL_SERVICE_NAME, d)
            await self.put_to_output_q(xmit)            
            
        # send list of items to add to Menu menu list
        if "add_controller_menu" in self.svc_parms:
            d = {"add_controller_menu" : self.svc_parms["add_controller_menu"]}
            xmit = XmitMsg(self.name,self.MENU_SVC_NAME, d)
            await self.put_to_output_q(xmit)           
        
        # just present during initial testing
        # eventually remove this loop?
        while True:
            # print("r",end="")
            # make sure no messages in my input queue
            await q_input.get()

