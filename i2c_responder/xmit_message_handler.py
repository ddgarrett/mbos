
"""
    XmitMsgHandler defines a handler function to call
    for messages from a particular service.
    
    Create new instance with:
        self.h = xmit_msg.XmitMsgHandler(size)
        
    where "size" is the number of handlers you will add.
    The list will be appended to if you add more
    handlers than size so this paramter is more for performance.
    
    To add a handler call
        self.h.add_handler(xmit_from, handler_func, rexmit_flag)
        
    where
        xmit_from    - defines who the xmit message is from
        handler_func - defines a function to receive the xmit message
                       if it was from xmit_from. MUST be an async function.
        rexmit_flag  - should xmit be forwarded to controller if xmit_from was matched
                       but handler_func return false?
    
    self.h.process_xmit(xmit, q_out) will traverse the list of handlers
    in the order defined until one returns True OR the rexmit flag is True.
    
    If a handler returns false and the rexmit_flag is true,
    the xmit will immediately be forwarded to the controller and True returned.
    Note that this skips any further checks of the handlers.
    Note also that the xmit_flag is NOT checked if the xmit_from was not matched.
    
    If message is not matched and Otherwise returns false.
    
    Example:
    
    # service_dht11 receives messages from service_ir but only handles the ir POWER_KEY
    # see service_dht11.py for complete program
    import xmit_msg
    import service_ir
    
    def __init__(self, svc_def):
        # only 1 handler. If not handled, forward to Controller
        self.h = xmit_msg.XmitMsgHandler(1)
        self.h.add_handler(xmit_ir_remote.XMIT_FROM_NAME,self.toggle_led,True)
        ... other init stuff
    
    # handle LED toggle xmit from IR input device
    async def toggle_led(self,xmit):
        if xmit.get_msg() == service_ir.POWER_BUTTON:
            ... do toggle LED stuff...
            return True
            
        return False
        
    # in main event loop
    async def run(self):
        ... run startup stuff
        q_in  = self.get_input_queue()
        q_out = self.get_output_queue()
        
        while True:
            while not q_in.empty():
                xmit = await q_in.get()
                handled = await self.h.process_xmit(xmit, q_out)
                
                ... if needed, handle xmit that wasn't handled
                ... but usually just ignore?
                
            ... remainder of run main loop
    
"""

XMIT_FROM_IDX    = 0
XMIT_HANDLER_IDX = 1
REXMIT_FLAG      = 2

# Name of controller service
CTL_SERVICE_NAME   = "controller"

class XmitMsgHandler:
    def __init__(self,size=5):
        self.handlers = [size]
        self.handler_cnt = 0
        
    def add_handler(self, xmit_from, handler_func, rexmit_flag):
        handler = [xmit_from, handler_func, rexmit_flag]
        if len(self.handlers) > self.handler_cnt:
            self.handlers[self.handler_cnt] = handler
        else:
            self.handlers.append(handler)
            
        self.handler_cnt = self.handler_cnt + 1
        
    async def process_xmit(self, xmit, q_out):
        xmit_fr = xmit.get_from()
        rexmit  = False
        
        for i in range(self.handler_cnt):
            if xmit_fr == self.handlers[i][XMIT_FROM_IDX]:
                handled = await self.handlers[i][XMIT_HANDLER_IDX](xmit)
                
                if handled:
                    return True
                
                # retransmit the message to the controller?
                if self.handlers[i][REXMIT_FLAG]:
                    await self.rexmit(xmit, q_out)
                    return True

        # No handlers returned true and no retransmits were triggered
        return False
    
    # retransmit a message to the controller
    async def rexmit(self, xmit, q_out):
        xmit.set_to(CTL_SERVICE_NAME)
        await q_out.put(xmit)
        
        
