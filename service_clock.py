"""
    Display and allow user to update the pico clock.
    
    Since Pico does not maintain time when disconnected
    from power, the time currently needs to be set every
    time it's run.
    
    This may change in the future if we get the RTC to work
    via I2C.

"""

from service import Service
import utf8_char
import uasyncio
import utime
import xmit_lcd

# All services classes are named ModuleService
class ModuleService(Service):
    
    WEEK_DAYS = ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', ]
    
    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.display_time_task = None

    async def gain_focus(self):
        await super().gain_focus()
        await self.start_time_display()

    async def lose_focus(self):
        await self.stop_time_display()
        await super().lose_focus()

    async def process_ir_input(self,xmit):
        if xmit.get_msg() == utf8_char.KEY_FORWARD_NEXT_PLAY:
            await set_time()
            
    async def start_time_display(self):
        if self.display_time_task == None:
            self.display_time_task = uasyncio.create_task(self.display_time())
        else:
            self.log_msg("*** ERROR: start_time_display() but task already running?")
        
    async def stop_time_display(self):
        if self.display_time_task != None:
            self.display_time_task.cancel()
            self.display_time_task = None
                
                
    # runs as a separate task
    # so we can go into a loop
    # as long as we have a uasyncio sleep
    async def display_time(self):
        
        msg = xmit_lcd.XmitLcd(fr=self.name)
        msg.clear_screen()
        await self.put_to_output_q(msg)
        
        # reduce flashing by only updating date if it changes
        prev_date_str = ""

        while True:
        
            time = utime.localtime()
            weekday = self.WEEK_DAYS[time[6]]
            
            date_str = "⏶ {month:>02d}/{day:>02d}/{year:>02d} {dow}".format(
                        year=time[0]%100, month=time[1], day=time[2], dow=weekday)
            
            time_str = "⏷ {HH:>02d}:{MM:>02d}:{SS:>02d}     ".format(
                        HH=time[3], MM=time[4], SS=time[5])
            
            xmit = xmit_lcd.XmitLcd(fr=self.name)
            
            if date_str != prev_date_str:
                prev_date_str = date_str
                xmit.set_cursor(0,0).set_msg(date_str)
                
            xmit.set_cursor(0,1).set_msg(time_str)
            await self.put_to_output_q(xmit)
            
            await uasyncio.sleep_ms(1000)
                        
    async def set_time(self):
        pass
        
        
        
        