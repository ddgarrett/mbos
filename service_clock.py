"""
    Display and allow user to update the pico clock.
    
    Since Pico does not maintain time when disconnected
    from power, the time currently needs to be set every
    time it's run.
    
    This may change in the future if we get the RTC to work
    via I2C.

"""

from service import Service
import machine
import utf8_char
import uasyncio
import utime
import xmit_lcd
import ds1307  # RTC Clock Module Interface

I2C_PORT = 0
I2C_SDA = 20
I2C_SCL = 21

# All services classes are named ModuleService
class ModuleService(Service):
    
    WEEK_DAYS = ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', ]
    
    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        self.display_time_task = None
        
        self.pico_rtc_set = False

    async def gain_focus(self):
        await super().gain_focus()
        
        if not self.pico_rtc_set:
            await self.set_time()
            self.pico_rtc_set = True
            
        await self.start_time_display()

    async def lose_focus(self):
        await self.stop_time_display()
        await super().lose_focus()
            
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
        
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.clear_screen()
        await self.put_to_output_q(xmit)
        
        # reduce flashing by only updating date if it changes
        prev_date_str = ""
        prev_time_str = ""

        while True:
        
            time = utime.localtime()
            weekday = self.WEEK_DAYS[time[6]]
            
            date_str = "⏶ {month:>02d}/{day:>02d}/{year:>02d} {dow}".format(
                        year=time[0]%100, month=time[1], day=time[2], dow=weekday)
            
            time_str = "⏷ {HH:>02d}:{MM:>02d}:{SS:>02d}".format(
                        HH=time[3], MM=time[4], SS=time[5])
            
            xmit = xmit_lcd.XmitLcd(fr=self.name)
            
            if date_str != prev_date_str:
                prev_date_str = date_str
                xmit.set_cursor(0,0).set_msg(date_str)
                
            self.update_time_display(prev_time_str,time_str,xmit)
            await self.put_to_output_q(xmit)
            prev_time_str = time_str
            
            await uasyncio.sleep_ms(1000)
                                
    # add the modified parts of the time string to the LCD xmit
    # sending entire string every second was resulting in missed IR input?
    def update_time_display(self,prev_time_str, time_str,xmit):
        
        if prev_time_str == "":
            xmit.set_cursor(0,1)
            xmit.set_msg(time_str)
            return
        
        if prev_time_str == time_str:
            return
        
        col = 0
        while (col < len(time_str)
          and  prev_time_str[col] == time_str[col]):
            col += 1
            
        xmit.set_cursor(col,1)
        xmit.set_msg(time_str[col:])

        
    # Read the date and time from the
    # battery backed up RTC module on the I2C bus and
    # use it to set the Pico builtin RTC which
    # does not have a battery.
    async def set_time(self):
        rtc = ds1307.ds1307(I2C_PORT,I2C_SCL,I2C_SDA)
        rtc.bus = self.get_i2c()
        
        t = rtc.read_time()
        
        rtc_pico = machine.RTC()
        rtc_pico.datetime(t)

        
        
        
