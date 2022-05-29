"""
    IR Service
    
    Receive IR signals from remote.
    
"""

from service import Service
import queue
import uasyncio
import ujson
import utime
import xmit_lcd
from ir_rx.nec import NEC_8
# from ir_rx.print_error import print_error  # Optional print of error codes
from ir_rx import IR_RX
from machine import Pin

# from xmit_ir_remote import XmitIrRemote

ir_obj = None

def sensor_callback(data, addr, ctrl):
    global ir_obj
    if data < 0:  # NEC protocol sends repeat codes.
        pass
        #print('Repeat code.')
    else:
        # print('********** Data {:02x} Addr {:04x} Ctrl {:02x}'.format(data, addr, ctrl))
        ir_obj.data = data
            
# All services classes are named ModuleService
class ModuleService(Service):

    def __init__(self, svc_parms):
        global ir_obj
        
        super().__init__(svc_parms)

        p = Pin(17, Pin.IN)
        self.ir_sensor = NEC_8(p,sensor_callback)
        # self.ir_sensor.error_function(print_error)

        self.e_cnt = {
           IR_RX.BADSTART : 0, IR_RX.BADBLOCK : 0, IR_RX.BADREP  : 0,
           IR_RX.OVERRUN  : 0, IR_RX.BADDATA  : 0, IR_RX.BADADDR : 0,
           0 : 0}
        
        self.e_msg = {
           IR_RX.BADSTART : "BS", IR_RX.BADBLOCK : "BB", IR_RX.BADREP  : "BR",
           IR_RX.OVERRUN  : "OR", IR_RX.BADDATA  : "BD", IR_RX.BADADDR : "BA",
           0 : "OT"}

        
        # self.ir_sensor.error_function(self.count_err)
         
        self.data = None
        self.lcd_on = 1
        ir_obj = self
        
        # read the ir key mapping file
        key_map_json = self.get_parm("key_map",None)
        # print("loading key maps from ", key_map_json)
        with open(key_map_json) as f:
            self.key_mapping = ujson.load(f)["hex_utf8_map"]
            # print(self.key_mapping)

    def count_err(self,data):
        if data in self.e_cnt:
            self.e_cnt[data] = self.e_cnt[data] + 1
            # print(self.e_msg[data],end=" ")
        else:
            self.e_cnt[0] = self.e_cnt[0] + 1
            # print(self.e_msg[0],end=" ")
            
        # print(data,end=" ")
        # print(self.e_cnt)
        
    
    async def run(self):
        self.run_check_task = uasyncio.create_task(self.check_ir_data())
        await super().run()
             
    # check to see if there is any IR data
    # if so, send the key
    async def check_ir_data(self):
        ts = utime.ticks_ms()
        
        while True:

            if (self.data != None
            and utime.ticks_diff(utime.ticks_ms(), ts) > 10):
                ts = utime.ticks_ms()
                await self.send_key(self.data)
                self.data = None
                
            await uasyncio.sleep_ms(10)

        
    # send a key to the focus service
    async def send_key(self, key):
        # print('Data {:02x} Addr {:04x} Ctrl {:02x}'.format(data, addr, ctrl))
        # translate hex key to UTF-8
        key_str = "{:02x}".format(key)
        # print("new service_ir: "+key_str)
        if key_str in self.key_mapping:
            # show hourglass to provide user feedback - character received
            xmit = xmit_lcd.XmitLcd(fr=self.name)
            xmit.dsp_hg()
            await self.put_to_output_q(xmit)
            
            # sound buzzer
            await self.send_msg("buzzer", "")
            
            # now send the character to "focus" service
            value = self.key_mapping[key_str]
            await self.send_msg("focus", value)
        else:
            await self.log_msg("skipped key not in utf-8 map: {:02x}".format(key))
        
