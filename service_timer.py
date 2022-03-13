"""
    Simple Timer Service
    
    Allows user to set N timers and a running total timer.
    
    Use case:
    BBQ - Turn chicken every 6 mintues for 25 to 35 minutes
        - Set 6 timers - turn chicken every 6 minutes
        
    1. Prompted for number of timers, followed by the ok/run button
    2. User enters 6, run/ok
    3. Presented: "#1 00:00" screen (min:sec)
    4. User enters 6 run/ok
    5. Presented: "#2 00:06" user enters a new number or just run/ok to keep that value
    6. After #6 timer entered
    7. Presented: "00:00:00 Press Ok/Run\nTimer 1: 00:00"
    8. After users presses ok/run running total goes up, timer goes down
    9. ok/enter will pause timers and display
    10. left arrow will exit ok/run resumes timers
    11. When timer 1 done display blinks - running total keeps running
    12. User presses ok/run to move onto next timer

"""

from service import Service
import uasyncio

import xmit_lcd
import xmit_message_handler

import utime
import utf8_char

import subsvc_total_time
import subsvc_timer

# All services classes are named ModuleService
class ModuleService(Service):
    async def run(self):
                
        while True:
            # make sure we have focus
            await self.await_gain_focus()
            
            # input number of timers
            timer_cnt = await self.get_timer_cnt()
            await self.define_and_run_timers(timer_cnt)
            await uasyncio.sleep_ms(0)
        
    # loop until we get a number between 1 and 9
    async def get_timer_cnt(self):
        async def prompt_timer_cnt():
            await self.prompt("⏶ Number\n⏷ of timers?")
            
        await prompt_timer_cnt()
        while True:
            xmit = await self.await_ir_input(gain_focus_func=prompt_timer_cnt)
            msg = xmit.get_msg()
            if msg < "1" or msg > "9":
                await self.prompt("⏶ Enter\n 1 thru 9\n⏷")
            else:
                return int(msg)
            
            await uasyncio.sleep_ms(0)
        
        
    # define then run specified number of timers
    async def define_and_run_timers(self,cnt):
        timers = []
        self.timer_objs = []
        
        for i in range(cnt):
            timers.append([0,0,0,0])
            self.timer_objs.append(subsvc_timer.CountDownTimer(self,3,0))
        
        # print(str(timer_objs)+"[0]: " + str(timer_objs[0]))
        
        # define timers
        for idx in range(cnt):
            
            # default timers after first to the previous timer
            if idx > 0 and timers[idx] == [0]*4 :
                timers[idx] = timers[idx-1].copy()
                
            await self.prompt("#"+str(idx+1)+" " + self.format_timer(timers[idx]))
            key = await self.get_timer(timers[idx])
            
            if key == utf8_char.KEY_REVERSE_BACK:
                return
            
            self.timer_objs[idx].init_value(timers[idx])
            
            await uasyncio.sleep_ms(0)
            

        
        xmit = await self.run_timers(timers)
        if xmit == None:
            print("no xmit received?")
        else:
            print("received msg: " + str(xmit.get_msg()))

        return
            
    # get a single timer - list of 4 single digit ints
    async def get_timer(self,timer):

        while True:
            timer_copy = timer.copy()
            
            xmit = await self.await_ir_input()
            key = xmit.get_msg()
            
            if (key == utf8_char.KEY_REVERSE_BACK
            and timer == [0]*4):
                return key
            
            if ((key == utf8_char.KEY_FORWARD_NEXT_PLAY or
                 key == utf8_char.KEY_OK)
            and  timer != [0]*4):
                return key
                
            if key >= "0" and key <= "9":
                n = int(key)
                timer[0] = timer[1]
                timer[1] = timer[2]
                timer[2] = timer[3]
                timer[3] = n
                
            if key == utf8_char.KEY_REVERSE_BACK:
                timer[3] = timer[2]
                timer[2] = timer[1]
                timer[1] = timer[0]
                timer[0] = 0
        
            if timer != timer_copy:
                await self.update_timer_display(timer)
        
    async def run_timers(self, timers):
        
        # run timers
        await self.prompt("#1")
        #await self.update_running_display(timers[0])
        
        # rundown_timer = subsvc_timer.CountDownTimer(self,3,0)
        # await rundown_timer.init_display(timers[0])
        rundown_timer = self.timer_objs[0]
        await rundown_timer.init_display()
        
        total_timer = subsvc_total_time.TotalTime(self,0,1)
        await total_timer.init_display()
                
        xmit = await self.await_ir_input(utf8_char.KEYS_FORWARD_REVERSE)                
        key = xmit.get_msg()
        
        if key == utf8_char.KEY_REVERSE_BACK:
            # TODO: confirm cancel before doing so
            return xmit
            
        tt_task = uasyncio.create_task(total_timer.run())
        rt_task = uasyncio.create_task(rundown_timer.run())
        
        idx = 0
        
        while True:
            await uasyncio.sleep_ms(250)
            xmit = await self.get_any_input()
            if xmit != None:
                #TODO: confirm cancel?
                # Allow skipping current timer?
                tt_task.cancel()
                rt_task.cancel()
                return xmit
            
            if rundown_timer.remain_ms <= 0:
                # rundown_timer exits when reaches 0
                idx += 1
                if idx >= len(self.timer_objs):
                    await self.prompt("Any key to exit",clear_screen=False)
                    await self.await_ir_input(control_keys=None)
                    tt_task.cancel()
                    return None
                
                await self.write_timer_number(idx)
                await self.prompt("#"+str(idx+1),clear_screen=False)
                
                rundown_timer = self.timer_objs[idx]
                await rundown_timer.init_display()
                
                # wait for any key to run next timer
                xmit = await self.await_ir_input(control_keys=None)                
                key = xmit.get_msg()
        
                if key == utf8_char.KEY_REVERSE_BACK:
                    # TODO: confirm cancel before doing so
                    return xmit
                
                rt_task = uasyncio.create_task(rundown_timer.run())
                    
        """
        for idx in range(len(timers)):
            rundown_timer = subsvc_timer.
            timer_tick_start = utime.ticks_ms()
            xmit = await self.run_timer(timers[idx],timer_tick_start)
            if xmit != None:
                tt_task.cancel()
                return xmit
    
        return None
        """
        
    # write timer number at position 0,0
    async def write_timer_number(self, idx):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(0,0)
        
        xmit.set_msg("#"+str((idx+1)))
        await self.put_to_output_q(xmit)
        
    async def run_timer(self, timer, timer_tick_start):
        
        timer_ms = self.calc_timer_ticks_ms(timer)
                 
        while True:
            await uasyncio.sleep_ms(1000)
            
            timer_fmt = self.decrement_timer_remain(timer_ms,timer_tick_start)
            await self.update_display_formatted(timer_fmt)
            
            xmit = await self.get_any_input()
            if xmit != None:
                #TODO: confirm cancel?
                # Allow skipping current timer?
                return xmit

    async def update_running_display(self, timer):
        await self.update_display_formatted(self.format_timer(timer))
        
    async def update_display_formatted(self, timer_formatted):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(3,0).set_msg(timer_formatted) 
        await self.put_to_output_q(xmit)
        
    def decrement_timer_remain(self, timer_ms,ticks_start):
        ticks = utime.ticks_ms()
        diff  = ticks-ticks_start
        remain_ms = timer_ms - diff
        if remain_ms < 0:
            return "00:00"
        
        sec_total = int(round(remain_ms/1000,0))
        sec = sec_total%60
        minutes_total = int((sec_total - sec)/60)
        minutes = minutes_total%60
        
        remain = "{:02d}:{:02d}".format(minutes,sec)
        return remain
        
    # given a timer as a list [m, m, s, s]
    # return the number of milliseconds in the timer
    def calc_timer_ticks_ms(self,timer):
        minutes = 10*timer[0] + timer[1]
        seconds = 10*timer[2] + timer[3]
        ms = ((minutes * 60) + seconds) * 1000
        return ms
        
    # send a message to the LCD,
    # clearing before displaying message
    async def prompt(self,msg,clear_screen=True,cursor=[0,0]):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        if clear_screen:
            xmit.clear_screen()
            if cursor != [0,0]:
                xmit.set_cursor(0,0)
        else:
            xmit.set_cursor(cursor[0],cursor[1])
            
        xmit.set_msg(msg)
        await self.put_to_output_q(xmit)    

    async def update_timer_display(self,timer):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(3,0).set_msg(self.format_timer(timer))
        await self.put_to_output_q(xmit)
        
    # 4 digit time format
    def format_timer(self,timer):
        d = "{0}{1}:{2}{3}"
        return d.format(*timer)


        

        
