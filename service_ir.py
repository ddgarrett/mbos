"""
    IR Service
    
    Receive IR signals from remote.
    
"""

from service import Service
import queue
import uasyncio
import ujson
import xmit_lcd
from ir_rx.nec import NEC_16
from machine import Pin

# from xmit_ir_remote import XmitIrRemote

ir_obj = None

def sensor_callback(data, addr, ctrl):
    global ir_obj
    if data < 0:  # NEC protocol sends repeat codes.
        pass
        #print('Repeat code.')
    else:
        # print('Data {:02x} Addr {:04x} Ctrl {:02x}'.format(data, addr, ctrl))
        ir_obj.data = data
            
# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        global ir_obj
        
        super().__init__(svc_parms)

        p = Pin(17, Pin.IN)
        self.ir_sensor = NEC_16(p,sensor_callback)
        # self.ir_sensor.error_function(sensor_error)
         
        self.data = None
        self.lcd_on = 1
        ir_obj = self
        
        # read the ir key mapping file
        key_map_json = self.get_parm("key_map",None)
        # print("loading key maps from ", key_map_json)
        with open(key_map_json) as f:
            self.key_mapping = ujson.load(f)["hex_utf8_map"]
            # print(self.key_mapping)

    async def run(self):
        q_input = self.get_input_queue()
        
        while True:

            # Don't expect any input messages, so
            # throw away all q_input messages.
            while not q_input.empty():
                xmit_msg = await q_input.get()
                
            if self.data != None:
                await self.send_key(self.data)
                self.data = None
                
            await uasyncio.sleep_ms(250)
             
    # send a key to the focus service
    async def send_key(self, key):
        # print('Data {:02x} Addr {:04x} Ctrl {:02x}'.format(data, addr, ctrl))
        # translate hex key to UTF-8
        key_str = "{:02x}".format(key)
        # print("new service_ir: "+key_str)
        if key_str in self.key_mapping:
            value = self.key_mapping[key_str]
            await self.send_msg("focus", value)
        else:
            await self.log_msg("skipped key not in utf-8 map: {:02x}".format(key))
        
