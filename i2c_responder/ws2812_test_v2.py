import machine
import utime
import math
from ws2812 import WS2812

import hsv_to_rgb

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

hf = 0

def set_led(h,s,v):
    h = min(float(h)/100.0,1.0)
    s = min(float(s)/100.0,1.0)
    v = min(float(v)/100.0,1.0)
    
    r,g,b = hsv_to_rgb.cnv(h,s,v)
    
    for j in range(8):
        # print(j,end=".")
        utime.sleep_ms(1)
        #r,g,b = hsv_to_rgb.cnv(hf,s,v)
        ws[j] = [r,g,b]
        ws.write()

    


while False:
    s = 100
    v = 25
    # hf = 0.0
    
    h = input("h: ")
    
    # print("h: '{}' hf: {} ".format(h,hf))
    
    if h == "=":
        hf = hf + .1
    elif h == "-":
        hf = hf - .1
    else:
        # h = float(h)/360.0
        hf = float(h)/100.0
        
    s = float(s)/100.0
    v = float(v)/100.0

    print("you entered: {} {} {}".format(hf,s,v))
    
    r,g,b = hsv_to_rgb.cnv(hf,s,v)
    
    """
    r,g,b = input("r,g,b: ").split()
    r = int(r)
    g = int(g)
    b = int(b)
    """
    
    print(" r g b: {} {} {}".format(r,g,b))
    
    utime.sleep_ms(100)
    for j in range(8):
        # print(j,end=".")
        utime.sleep_ms(1)
        r,g,b = hsv_to_rgb.cnv(hf,s,v)
        ws[j] = [r,g,b]
        ws.write()
        
    print("")





"""

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

# while True:
n = 10
m = 30
for i in range(n/2):
    ip = i/n * 2
    for j in range(m):
        r,g,b = hsv_to_rgb.cnv(ip,1,j/m)
        for j in range(8):
            ws[j] = [r,g,b]
            ws.write()
        utime.sleep(.05)
        print(i,ip,j/m)
        
    for j in range(m,0,-1):
        r,g,b = hsv_to_rgb.cnv(ip,1,j/m)
        for j in range(8):
            ws[j] = [r,g,b]
            ws.write()
        utime.sleep(.05)
        print(i,ip,j/m)
        
    utime.sleep(.5)
    
    ip = abs(i/n-0.5)
    for j in range(int(m/2)):
        v = abs(j)/m * 2
        r,g,b = hsv_to_rgb.cnv(ip,1,v)
        for j in range(8):
            ws[j] = [r,g,b]
            ws.write()
        utime.sleep(.05)      
        print(i,ip,v)
        
    for j in range(int(m/2),0,-1):
        v = abs(j)/m * 2
        r,g,b = hsv_to_rgb.cnv(ip,1,v)
        for j in range(8):
            ws[j] = [r,g,b]
            ws.write()
        utime.sleep(.05)      
        print(i,ip,v)
        
    utime.sleep(.5)
    
"""


"""
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