"""
    Service Superclass
    
"""
from xmit_message import XmitMsg
import queue
import uasyncio
import utf8_char
import xmit_lcd

class Service:
    
    """
        Superclass of all Services.

        svc_parms = the parameters defined by the .json file for this Service.
                  
        Note: parameters must include at a minimum:
        - name   - logical name of service
        - module - name of the file with the definition for a ModuleService class
        
        Service subclasses may also have additional parms such as pin definitions.
        Those will be available to the service via a call to
            self.get_parm(name,default)
        where 'name' is the parm name and default is the default value if name was not
        specified in the .json file.
                
        JSON file example:
            {"name":"log", "module":"service_print",
                 "q_in_size":1000, "q_out_size":5 },
        
    """
    
    ##
    ##  Messages below are sent to or from the "controller" service 
    ##
    
    # Name of some services
    CTL_SERVICE_NAME   = "controller"
    IR_REMOTE_SVC_NAME = "ir_remote"
    
    # Messages sent by controller to other services
    CTL_GAIN_FOCUS_MSG = "gain focus"
    CTL_LOSE_FOCUS_MSG = "lose focus"
    
    # Messages sent by other services to controller
    CTL_PUSH_FOCUS_MSG = "push focus"  # push name of current focus service onto stack
                                       # focus goes to send from service
    CTL_XFER_FOCUS_MSG = "xfer focus"  # transfer focus to send from service, without a push
    CTL_POP_FOCUS_MSG  = "pop focus"   # pop name on top of stack to make it the current focus
    
    def __init__(self, svc_parms):
        self.svc_parms = svc_parms
        
        self.name = svc_parms['name']
        self.input_queue = queue.Queue(self.get_parm('q_in_size',5))
        self.output_queue = queue.Queue(self.get_parm('q_out_size',5))
        
        self.has_focus = False
        self.blink_rate = 0
        
        # print(self.name + ": super().__init__(...)")
        
    def get_input_queue(self):
        return self.input_queue

    def get_output_queue(self):
        return self.output_queue
    
    async def put_to_output_q(self, xmit):
        await self.output_queue.put(xmit)


    # By default, polls input queue waiting for IR input.
    # Any IR input is passed to the self.process_ir_input(xmit) method.
    # Calls self.gain_focus() and lose_focus() when focus is gained or lost.
    # Simple apps just have to override the gain_focus()
    # and process_ir_input(xmit) methods.
    async def run(self):
        while True:
            
            xmit = await self.await_ir_input()
            await self.process_ir_input(xmit)
            
            await uasyncio.sleep_ms(0)
            
    ##  send message to another service
    async def send_msg(self, to, msg):
        xmit = XmitMsg(self.name,to,str(msg))
        await self.put_to_output_q(xmit)
        
    # send message to the log service
    async def log_msg(self, msg):
        await self.send_msg("log", msg)
        
    # make self the current focus service, pushing current focus service onto the stack
    async def push_focus(self):
        await self.send_msg(self.CTL_SERVICE_NAME,self.CTL_PUSH_FOCUS_MSG)
        
    # make self current focus, but do NOT push current focus onto stack
    async def xfer_focus(self):
        await self.send_msg(self.CTL_SERVICE_NAME,self.CTL_XFER_FOCUS_MSG)
        
    # relinquish focus by current focus and make top of focus stack the current focus
    async def pop_focus(self):
        await self.send_msg(self.CTL_SERVICE_NAME,self.CTL_POP_FOCUS_MSG)
        
    ##
    ## Common Recieve Messages for Gain and Lose Focus
    ##   returns True if the specific message was received
    ##   requires ENTIRE queue transmission (xmit), not just the message
        
    def gain_focus_msg(self, q_xmit):
        if (q_xmit.get_from() == self.CTL_SERVICE_NAME) \
        and (q_xmit.get_msg() == self.CTL_GAIN_FOCUS_MSG):
            return True
        
        return False
        
    def lose_focus_msg(self, q_xmit):
        if (q_xmit.get_from() == self.CTL_SERVICE_NAME) \
        and (q_xmit.get_msg() == self.CTL_LOSE_FOCUS_MSG):
            return True
        
        return False
    
    """
        Simple services can just override the following three methods.
        
        gain_focus() - initialize and begin updating, if any, of LCD
                     - start any asynchronous tasks
                   
        lose_focus() - cleanup, such as cancelling any started tasks
        
        process_ir_input(xmit) - handle any IR input not handled by await_ir_input().
                     By default await_ir_input() will forward any control keys automatically
                     but this can be overridden by overriding await_ir_input() and calling
                     super().await_ir_input(...) with custom parms.

    """
    ### common gain focus and lose focus methods
    async def gain_focus(self):
        self.has_focus = True
        
    async def lose_focus(self):
        self.has_focus = False
        
    async def process_ir_input(self,xmit):
        pass
        
    # retransmit a message to the controller
    async def rexmit(self, xmit):
        xmit.set_to(self.CTL_SERVICE_NAME)
        await self.get_output_queue().put(xmit)
                
    # Loop that does not return until the service has gained focus
    async def await_gain_focus(self):
        
        if self.has_focus:
            return
        
        q_in = self.get_input_queue()
                
        while True:
            while not q_in.empty():
                xmit = await q_in.get()
                if self.gain_focus_msg(xmit):
                    self.has_focus = True
                    return
            
            await uasyncio.sleep_ms(0)
    
    # Check the input queue for any input.
    # If found, return the queue
    # else return None
    async def get_any_input(self):
        q_in = self.get_input_queue()
        if not q_in.empty():
            return await q_in.get()
        
        return None
        
    #
    # Loop that waits until we get input from IR Reciever
    #
    # If lose focus, wait for gain focus
    # and ignore all other msg
    #
    # When gain/lose focus, the specified gain/lose focus functions are called.
    # By default this is the self.gain_focus() and self.lose_focus() methods
    # 
    # Optional accept_keys allows specification of a list of acceptable input keys.
    # If specified, will only return values in that list.
    # Default of accept_keys=None will accept any key 
    #
    # Optional control_keys allow navigation via the Menu service,
    # while waiting for user input. This can cause problems if your
    # gain_focus_func does not refresh the display.
    # Set control_keys=None to disable navigation away from the current display. 
    #
    async def await_ir_input(self,
                             accept_keys=None,
                             control_keys=utf8_char.KEYS_NAVIGATE,
                             gain_focus_func=None,
                             lose_focus_func=None):
        
        # below required because we can not default
        # the functions to "self.x"
        if gain_focus_func == None:
            gain_focus_func = self.gain_focus
        if lose_focus_func == None:
            lose_focus_func = self.lose_focus
            
        q_in = self.get_input_queue()
        
        # make sure we already have focus
        # await self.await_gain_focus()
        
        while True:
            while not q_in.empty():
                xmit = await q_in.get()
                if self.lose_focus_msg(xmit):
                    await lose_focus_func()
                    await self.await_gain_focus()
                    await gain_focus_func()
                    
                elif self.gain_focus_msg(xmit):
                    await gain_focus_func()
                    
                elif xmit.get_from() == self.IR_REMOTE_SVC_NAME:

                    # retransmit control keys to controller
                    if control_keys != None and xmit.get_msg() in control_keys:
                        await self.rexmit(xmit)
                        
                    elif accept_keys == None or xmit.get_msg() in accept_keys:
                        return xmit
                    
            await uasyncio.sleep_ms(0)
        
    ## Get an instance of the I2C object using standard parms
    def get_i2c(self):
        return self.get_parm("i2c",None)
          
            
    ## return a value for a parameter in the original .json file
    ##    or the default parm value if parm was not in the .json file
    def get_parm(self, parm_name, parm_default):
        if parm_name in self.svc_parms:
            return self.svc_parms[parm_name]
        
        defaults = self.svc_parms["defaults"]
        if parm_name in defaults:
            return defaults[parm_name]
        
        return parm_default
        
                
        

    
