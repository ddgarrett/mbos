"""
    Display MPU6050 Gyro Data.

"""

from service import Service
import machine
import utf8_char
import uasyncio
import utime
import xmit_lcd
import ds1307  # RTC Clock Module Interface

from imu import MPU6050


# All services classes are named ModuleService
class ModuleService(Service):
    
    def __init__(self, svc_parms):
        super().__init__(svc_parms)
        
        self.display_task = None
        
        self.imu = None
        self.adj_x = self.get_parm("adj_x",0)


    async def gain_focus(self):
        await super().gain_focus()
        
        if self.imu == None:       
            dev_addr = self.get_parm("device_addr",0)
            self.imu = MPU6050(self.get_i2c_bus_1(),device_addr=dev_addr)
        
        if self.display_task == None:
            self.display_task = uasyncio.create_task(self.display_data())
        else:
            self.log_msg("*** ERROR: start_data() but task already running?")


    async def lose_focus(self):
        if self.display_task != None:
            self.display_task.cancel()
            self.display_task = None
            
        await super().lose_focus()
            
                
    # runs as a separate task
    # so we can go into a loop
    # as long as we have a uasyncio sleep
    async def display_data(self):
        
        ts = utime.ticks_ms()
                    
        xmit = xmit_lcd.XmitLcd(fr=self.name)
        xmit.clear_screen()
        msg = "⏶  {: >4}  {: >4}  {: >4}  ".format("°X", "°Y", "°F")
        xmit.set_cursor(0,0).set_msg(msg)
        xmit.set_cursor(0,1).set_msg("⏷ ")
        await self.put_to_output_q(xmit)
        
        prev_msg = ""

        while True:
        
            if utime.ticks_diff(utime.ticks_ms(), ts) > 1000:
                
                ts = utime.ticks_ms()
                
                ax=int(round(self.imu.accel.x*90/4))
                ay=int(round(self.imu.accel.y*90/4))
                temp=int(round((self.imu.temperature* 1.8 + 32)))
                                
                # try rounding to the nearest 4 degrees
                ax = ax*4 + self.adj_x
                ay = ay*4

                axs   = "{:d}".format(ax)
                ays   = "{:d}".format(ay)
                temps = "{:d}".format(temp)
                
                msg = "{: >4} {: >4} {: >4}  ".format(axs,ays,temps)
               
                if msg != prev_msg:
                    prev_msg = msg
                    
                    xmit = xmit_lcd.XmitLcd(fr=self.name)
                    xmit.set_cursor(2,1).set_msg(msg)
                    
                    await self.put_to_output_q(xmit)
            
            await uasyncio.sleep_ms(0)
                                
        
        
        
