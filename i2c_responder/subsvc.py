"""
    Service Superclass
    
"""
from xmit_message import XmitMsg
import queue
import uasyncio
import utf8_char
import xmit_lcd

class Subservice:
    
    """
        Superclass of all Subservices.

        Parms:
        service = the service creating this subservice
        
        All parameters and queues are via the creating service.
        It's up to the creating service to call the gain/lose
        focus methods on the subservice.
        
        The subservice may use the creating service
        await_ir_input(...) method to wait for IR input.
        
                          
    """
    
    
    def __init__(self, service):
        self.service = service
        self.has_focus = False
        self.prev_display = "                    "
        
        
    def get_svc(self):
        return self.service
    
    def reset_prev_display(self):
        self.prev_display = "                    "
            
    ### Common gain focus and lose focus methods
    ### It's up to the creating service to call these
    async def gain_focus(self):
        self.has_focus = True
        
    async def lose_focus(self):
        self.has_focus = False
        
    async def process_ir_input(self,xmit):
        pass
                        
    # Loop that does not return until the service has
    # given this subservice focus
    async def await_gain_focus(self):
                        
        while True:
            if self.has_focus:
                return true
            
            await uasyncio.sleep_ms(50)
        
    #
    # Loop that waits until we get input from IR Reciever
    #
    # Use with care since only one subservice at a time should use this
    # and it should not be used while the creating service is using it.
    #
    async def await_ir_input(self,
                             accept_keys=None,
                             control_keys=utf8_char.KEYS_NAVIGATE,
                             gain_focus_func=None,
                             lose_focus_func=None):
        
        return await self.service.await_ir_input(accept_keys,control_keys,
                                                 gain_focus_func,lose_focus_func)

    # Update a subservice display taking care to only
    # write what's changed.
    # WARNING: currently all messages must be the same length
    # and no longer than 20 characters
    async def update_display(self,fmt_display):
        
        if fmt_display == self.prev_display:
            return
        
        col = 0
        while (col < len(fmt_display)
          and  self.prev_display[col] == fmt_display[col]):
            col += 1

        self.prev_display = fmt_display
        lcd_x = col + self.lcd_x
        
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(lcd_x,self.lcd_y)
        
        xmit.set_msg(fmt_display[col:])
        await self.service.put_to_output_q(xmit)
        
    ## return a value for a parameter in the original .json file
    ##    or the default parm value if parm was not in the .json file
    def get_parm(self, parm_name, parm_default):
        return self.service.get_parm(parm_name,parm_default)
        
                
        

    
