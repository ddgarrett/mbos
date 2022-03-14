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
                await self.prompt("⏶ Enter\n⏷ 1 thru 9")
            else:
                return int(msg)
            
            await uasyncio.sleep_ms(0)
        
        
    # define then run specified number of timers
    async def define_and_run_timers(self,cnt):
        
        self.timer_objs = []
        
        for i in range(cnt):
            self.timer_objs.append(subsvc_timer.CountDownTimer(self,3,0))
        
        default_timer = [0,0,0,0]
        
        # define timers
        for idx in range(cnt):
            
            await self.prompt("#"+str(idx+1)+" ")
            key = await self.timer_objs[idx].input_timer(default_timer)
            
            if key == utf8_char.KEY_REVERSE_BACK:
                return
            
            default_timer = self.timer_objs[idx].timer.copy()
            await uasyncio.sleep_ms(0)
        
        # Now run the timers
        xmit = await self.run_timers()
        if xmit != None:
            print("received msg: " + str(xmit.get_msg()))

        return
                
    async def run_timers(self):
        
        # run timers
        await self.prompt("#1")
        
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
            xmit = await self.get_any_input() #non blocking
            
            # TODO: confirm it's a back key
            # if ok or forward, pause...
            # if second forward, skip current timer and go to next
            # blank out prompt in either case
            if xmit != None:
                #TODO: confirm cancel?
                # Allow skipping current timer?
                tt_task.cancel()
                rt_task.cancel()
                return xmit
            
            if rundown_timer.remain_ms <= 0:
                
                xmit = await self.timer_expired()
                if xmit.get_msg() == utf8_char.KEY_REVERSE_BACK:
                    return xmit
                
                # rundown_timer.run() exits when reaches 0
                idx += 1
                if idx >= len(self.timer_objs):
                    await self.prompt("Any key to exit",clear_screen=False)
                    await self.await_ir_input(control_keys=None)
                    tt_task.cancel()
                    return None
                
                # await self.write_timer_number(idx)
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
    
    # blink LCD and await user input
    async def timer_expired(self):
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        
        xmit.blink_slow()
        await self.put_to_output_q(xmit)
        
        xmit = await self.await_ir_input(control_keys=None)                
        key = xmit.get_msg()
        
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        await self.put_to_output_q(
                   xmit.blink_off().
                   set_cursor(9,0).
                   set_msg("next ⏵")
                   )
 
        xmit_exit = await self.await_ir_input(control_keys=None)                
        
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.set_cursor(9,0).set_msg("            ")
        await self.put_to_output_q(xmit)
        
        return xmit_exit
    
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
