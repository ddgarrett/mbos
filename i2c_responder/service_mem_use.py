"""
    Show Disk and Memory Use
    
"""

import os
import gc

from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

# All services classes are named ModuleService
class ModuleService(Service):

    async def gain_focus(self):
        await super().gain_focus()
        await self.show_mem_use()

    async def show_mem_use(self):
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen().set_msg("⏶ " + self.df() + "\n⏷ " + self.free())
        await self.put_to_output_q(msg)    

    # disk free space
    def df(self):
        s = os.statvfs('//')
        blk_size = s[0]
        total_mb = (s[2] * blk_size) / 1048576
        free_mb  = (s[3] * blk_size) / 1048576
        pct = free_mb/total_mb*100
        # return ('Disk Total: {0:.2f} MB Free: {1:.2f} ({2:.2f}%)'.format(total_mb, free_mb, pct))
        return ('DFr {0:.2f}MB {1:.0f}%'.format(free_mb, pct))

    def free(self):
        gc.collect() # run garbage collector before checking memory 
        F = gc.mem_free()
        A = gc.mem_alloc()
        T = F+A
        P = '{0:.0f}%'.format(F/T*100)
        return ('MFr {0:,} {1}'.format(F,P))


