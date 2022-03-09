"""
    Use sonic echo to determine distance.
    
    From https://www.tomshardware.com/how-to/raspberry-pi-pico-ultrasonic-sensor

"""

from machine import Pin
import utime

trigger = Pin(15, Pin.OUT)
echo = Pin(14, Pin.IN)

def ultra():
    # make sure the trigger is low
    trigger.low()
    utime.sleep_us(2)
    
    # set trigger high for 5 micro seconds
    trigger.high()
    utime.sleep_us(5)
    trigger.low()
    
    # wait for echo to go high
    while echo.value() == 0:
        signaloff = utime.ticks_us()
        
    # count how long it remains high
    while echo.value() == 1:
        signalon = utime.ticks_us()
        
    # how far the sound traveled to and from object
    # based on how far it went in 5 microseconds
    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2
    distance = distance * 0.393701  # convert to inches
    
    if distance > 18 :
        distance = distance /12
        distance = "{:.2f} ft".format(distance)
    else:
        distance = "{:.2f} inches".format(distance)
    
    print("The distance from object is ",distance)
    

while True:
    ultra()
    utime.sleep(1)