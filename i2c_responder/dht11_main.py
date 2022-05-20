from machine import Pin
import time
from dht11 import DHT11, InvalidChecksum
 
sensor = DHT11(Pin(16, Pin.OUT, Pin.PULL_DOWN))
 
last_temp = 0
last_humid = 0
while True:
    try: 
        temp = sensor.temperature * 1.8 + 32
        humidity = sensor.humidity
        
        temp -= 2.5
        humidity += 10
        
        if last_temp != temp or last_humid != humidity:
            last_temp = temp
            last_humid = humidity
            print("")
            print("Temperature: {:.1f}°F   Humidity: {:.0f}% ".format(temp, humidity))
        else:
            print(".",end="")

    except Exception as e:
        # update_ok = False
        # await self.log_msg(e)
        print("")
        print(e)
        # pass
    # temp = sensor.temperature * 1.8 + 32
    # humidity = sensor.humidity
    # print("Temperature: {:.1f}°F   Humidity: {:.0f}% ".format(temp, humidity))
    time.sleep(2)