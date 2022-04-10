import machine
import utime
import math
from ws2812 import WS2812

ws = WS2812(machine.Pin(0),8)
ws[0] = [64,154,227]
ws[1] = [128,0,128]
ws[2] = [50,150,50]
ws[3] = [255,30,30]
ws[4] = [0,128,255]
ws[5] = [99,199,0]
ws[6] = [128,128,128]
ws[7] = [255,100,0]
ws.write()

utime.sleep(2)

n = 256  # number of steps
TWO_PI = 3.14159*2


for i in range(n):
    r = int(round((128 + math.sin(i*TWO_PI/n + 0) + 127),0))
    g = int(round((128 + math.sin(i*TWO_PI/n + TWO_PI/3) + 127),0))
    b = int(round((128 + math.sin(i*TWO_PI/n + 2*TWO_PI/3) + 127),0))

    
    for j in range(8):
        ws[j] = [r,g,b]
        
    ws.write()
    print("{} {} {} {}     ".format(i,r,g,b),end="\r")
    utime.sleep(.1)


"""
n = [0,32,64,96,128,159,191,223,255]

for r in n:
    for g in n:
        for b in n:
            for i in range(8):
                ws[i] = [r,g,b]
            ws.write()
            utime.sleep(.1)
            print(r,g,b,end="\r")
"""        

"""
for i in range(63):
    s = ws[7]
    for j in range(7):
        ws[7-j] = ws[7-j-1]
        
    ws[0] = s
    
    ws.write()
    utime.sleep(.1)

"""

# ws = WS2812(machine.Pin(0),8)
ws[0] = [0,0,0]
ws[1] = [0,0,0]
ws[2] = [0,0,0]
ws[3] = [0,0,0]
ws[4] = [0,0,0]
ws[5] = [0,0,0]
ws[6] = [0,0,0]
ws[7] = [0,0,0]
ws.write()