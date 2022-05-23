"""
    Keypad Service
    
    Emulate IR Receiver.
    Todo: change ir input stuff to be more generic so
    both Keypad Service and IR Service work without kluges.
    
"""

from service import Service
import queue
import uasyncio
import utime
import xmit_lcd
from xmit_message import XmitMsg
from machine import Pin

# CONSTANTS
KEY_UP   = const(0)
KEY_DOWN = const(1)
            
# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        super().__init__(svc_parms)

        self.keys = [['1', '2', '3', ''],
                     ['4', '5', '6', '⏴'],
                     ['7', '8', '9', '⏶'],
                     ['*', '0', '#', '⏷']]

        # Pin names keypad
        self.rows = [6,7,8,9]
        self.cols = [10,11,12,13]

        # set pins for rows as outputs
        self.row_pins = [Pin(pin_name, mode=Pin.OUT) for pin_name in self.rows]

        # set pins for cols as inputs
        self.col_pins = [Pin(pin_name, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_name in self.cols]




    async def run(self):
        # make sure row output pins are low
        for row in range(0,4):
            self.row_pins[row].low()
            
        q_input = self.get_input_queue()
        last_key = None
        last_key_cnt = 1
        
        while True:

            # Don't expect any input messages, so
            # throw away all q_input messages.
            while not q_input.empty():
                xmit_msg = await q_input.get()
                
            key = self.scan()
                
            if key != None:
                if key != last_key:
                    last_key = key
                    last_key_cnt = 1
                # ensure key pressed for 2 cycles
                elif last_key_cnt == 1:
                    last_key_cnt = 2
                    # print("Key Pressed", key)
                    await self.send_key(last_key)
                    
            else:
                last_key = None
                
            await uasyncio.sleep_ms(100)
            
             
    # send a key to the focus service
    async def send_key(self, key):

        # show hourglass to provide user feedback - character received
        xmit = xmit_lcd.XmitLcd(fr="ir_remote")
        xmit.dsp_hg()
        await self.put_to_output_q(xmit)           
        
        # now send the character to "focus" service
        xmit = XmitMsg("ir_remote","focus",key)
        await self.put_to_output_q(xmit)
        

    # return first key down found,
    # or None if no key down
    def scan(self):
        for row in range(4):
            self.row_pins[row].high()
            for col in range(4):
                if self.col_pins[col].value() == KEY_DOWN:
                    self.row_pins[row].low()
                    return self.keys[row][col]

            # reset row pin
            self.row_pins[row].low()

        return None

        
        

