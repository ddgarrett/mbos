# demo 1

from machine import Pin
import time

# CONSTANTS
KEY_UP   = const(0)
KEY_DOWN = const(1)

keys = [['1', '2', '3', 'A'], ['4', '5', '6', 'B'], ['7', '8', '9', 'C'], ['*', '0', '#', 'D']]

# Pin names for Pico
rows = [6,7,8,9]
cols = [10,11,12,13]

# set pins for rows as outputs
row_pins = [Pin(pin_name, mode=Pin.OUT) for pin_name in rows]

# set pins for cols as inputs
col_pins = [Pin(pin_name, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_name in cols]

def init():
    for row in range(0,4):
        # for col in range(0,4):
        row_pins[row].low()

# return first key down found,
# or None if no key down
def scan():
    for row in range(4):
        row_pins[row].high()
        for col in range(4):
            if col_pins[col].value() == KEY_DOWN:
                row_pins[row].low()
                return keys[row][col]

        # reset row pin
        row_pins[row].low()

    return None

print("starting")

# set all the columns to low
init()

last_key = None
last_key_cnt = 0



while True:
    
    key = scan()
    if key != None:
        if key != last_key:
            last_key = key
            last_key_cnt = 1
        # ensure key pressed for 2 cycles
        elif last_key_cnt == 1:
            last_key_cnt = 2
            print("Key Pressed", key)
            
    else:
        last_key = None
            
                
    time.sleep_ms(100)
    
"""
         
while True:
    for row in range(4):
        for col in range(4):
            key = scan(row, col)
            if key == KEY_DOWN:
                print("Key Pressed", keys[row][col])
                last_key_press = keys[row][col]
"""