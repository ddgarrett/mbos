"""
    Subservice Total Time
    
    Keeps a running total timer in the format HH:MM:SS
    
    To use:
      timer = subsvc_total_time.ModuleSubservice(self,2,1) # display col 2, row 1
      timer_task = uasyncio.create_task(timer.run())
      ...
      timer_task.cancel()
      
    
    Parms:
      - service - the service creating this subservice
      - lcd_x   - the column to display the timer
      - lcd_y   - the row to display the timer
    
    This subservice will continue to run until canceled.

"""

from subsvc import Subservice
import uasyncio
import utime

import xmit_lcd
import xmit_message_handler

class TotalTime(Subservice):
    
    def __init__(self, service, lcd_x, lcd_y):
        super().__init__(service)
        self.lcd_x = lcd_x
        self.lcd_y = lcd_y
        self.ticks_start = 0

        self.name = service.name + ".subsvc_total_time"
        
    
    async def init_display(self):
        await self.update_display("00:00:00")
                
    # starts display of a timer at the specified
    # row and column based on time since ticks
    async def run(self):
        
        self.ticks_start = utime.ticks_ms()

        while True:
            await uasyncio.sleep_ms(1000)
            timer_fmt = self.increment_timer()
            await self.update_display(timer_fmt)        
        
    # set the total_timer based on # ticks since ticks_start
    def increment_timer(self):
        ticks = utime.ticks_ms()
        diff = ticks - self.ticks_start
        
        sec_total = int(round(diff/1000,0))
        sec = sec_total%60
        minutes_total = int((sec_total - sec)/60)
        minutes = minutes_total%60
        hours = int((minutes_total - minutes)/60)
        
        elapsed = "{:02d}:{:02d}:{:02d}".format(hours,minutes,sec)
        return elapsed

        

    
        
        

        
