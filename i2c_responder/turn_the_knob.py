import machine
from machine import Pin
import utime

"""
    3.4.12 Turn the Knob (p. 93)
    
    Converted to use Arduino kit sound sensor.
    
    Read both analog signal and digital trigger
    from sound receiver module.
    
"""

potentiometer = machine.ADC(28)
trigger = Pin(5,Pin.IN,Pin.PULL_UP)
# led = machine.PWM(Pin(14))
# led.freq(1000)

n = [0.0]*10
i = 0

while True:
    t = trigger.value()
    if t:
        value=potentiometer.read_u16()
        print(value,end="(")
        print(t,end="),")
        
        n[i] = value
        i = i + 1
        if i >= len(n):
            i = 0
            a = int(round((sum(n)/len(n)),0))
            print(a,min(n),max(n))
                
        # led.duty_u16(value)
    utime.sleep_ms(50)
