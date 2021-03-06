"""
    Subservice To Run a Prespecified Timer
    
    Allows definition of a timer in mm:ss format.
    Then allows a timer to run from a preset time to 0.
    
    
    To use:
      # display col 3, row 0
      # slow blink at 60 seconds, fast blink last 30 seconds
      timer = subsvc_timer.ModuleSubservice(self,3,0,60,30)
      timer.input_time()
      timer.set_expire_callback(service.func)
      timer_task = uasyncio.create_task(timer.run())
      timer.pause() # called it the timer is paused
      
    When timer goes to zero it will call the expire_callback function
    then exit.
      
    
    Parms:
      - service - the service creating this subservice
      - lcd_x   - the column to display the timer
      - lcd_y   - the row to display the timer
      - slow_blink - seconds remaining to cause display to blink slowly
      - fast_blink - seconds remaining to cause display to blink fast
    
    This subservice will continue to run until it goes to zero or is canceled.
    When it hits zero, it will call the expire callback function and then exit.

"""

from subsvc import Subservice
import uasyncio
import utime

import xmit_lcd
import xmit_message_handler

import utf8_char


class CountDownTimer(Subservice):
    
    def __init__(self, service, lcd_x, lcd_y):
        super().__init__(service)
        self.lcd_x = lcd_x
        self.lcd_y = lcd_y
        
        self.timer = [0,0,0,0] # mm, ss
        self.name = service.name + ".subsvc_timer"
        self.remain_ms = 100_000
        
    # allow input of a new timer digits
    async def input_timer(self, default_value):
        
        if self.timer == [0,0,0,0]:
            self.timer = default_value
        
        self.reset_prev_display()
        
        while True:
            await self.update_display(self.format_timer())
            
            xmit = await self.service.await_ir_input()
            key = xmit.get_msg()
                
            # back key when timer is all zeros?
            if (key == utf8_char.KEY_REVERSE_BACK
                and self.timer == [0]*4):
                    return key
                
            # forward or ok key when timer is not all zeros?
            if ((key == utf8_char.KEY_FORWARD_NEXT_PLAY or
                 key == utf8_char.KEY_OK)
            and  self.timer != [0]*4):
                    return key
            
            # add a digit
            if key >= "0" and key <= "9":
                n = int(key)
                self.timer[0] = self.timer[1]
                self.timer[1] = self.timer[2]
                self.timer[2] = self.timer[3]
                self.timer[3] = n
                    
            # remove a digit
            if key == utf8_char.KEY_REVERSE_BACK:
                self.timer[3] = self.timer[2]
                self.timer[2] = self.timer[1]
                self.timer[1] = self.timer[0]
                self.timer[0] = 0
            
    # initial display of countdown timer,
    # before it starts running
    async def init_display(self):
        self.calc_timer_ticks_ms()
        self.reset_prev_display()
        await self.update_display(self.format_timer())
    
    # given a timer as a list [m, m, s, s]
    # return the number of milliseconds in the timer
    def calc_timer_ticks_ms(self):
        minutes = 10*self.timer[0] + self.timer[1]
        seconds = 10*self.timer[2] + self.timer[3]
        self.timer_ms = ((minutes * 60) + seconds) * 1000

    # 4 digit time format
    def format_timer(self):
        d = "{0}{1}:{2}{3}"
        return d.format(*(self.timer))
                
    # starts display of a timer at the specified
    # row and column based on time since ticks
    async def run(self):
        
        self.ticks_start = utime.ticks_ms()
        self.update_remain_ms()

        while self.remain_ms > 0:
            await uasyncio.sleep_ms(1000)
            self.update_remain_ms()
            timer_fmt = self.fmt_remain_ms()
            await self.update_display(timer_fmt)        
        
    # format remaining milliseconds as mm:ss
    def fmt_remain_ms(self):
        if self.remain_ms <= 0:
            return "00:00"
        
        sec_total = int(round(self.remain_ms/1000,0))
        sec = sec_total%60
        minutes_total = int((sec_total - sec)/60)
        minutes = minutes_total%60
        
        remain = "{:02d}:{:02d}".format(minutes,sec)
        return remain

    # calculate number of milliseconds remaining on timer
    def update_remain_ms(self):
        ticks = utime.ticks_ms()
        diff  = ticks-self.ticks_start
        self.remain_ms = self.timer_ms - diff
        


        

    
        
        

        
