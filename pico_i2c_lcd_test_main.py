import utime

import machine
from machine import I2C
# from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

import utf8_char

I2C_ADDR     = 0x27
I2C_NUM_ROWS = 4 # 2
I2C_NUM_COLS = 20 # 16

# degree symbol
degreeSymbol = [
0b00110,
0b01001,
0b01001,
0b00110,
0b00000,
0b00000,
0b00000,
0b00000
]

reverseBack = [
  0b00010,
  0b00110,
  0b01110,
  0b11110,
  0b01110,
  0b00110,
  0b00010,
  0b00000
]

forwardNextPlay = [
  0b01000,
  0b01100,
  0b01110,
  0b01111,
  0b01110,
  0b01100,
  0b01000,
  0b00000
]

KEY_INCREASE = [
    0b00000,
    0b00000,
    0b00100,
    0b01110,
    0b11111,
    0b00000,
    0b00000,
    0b00000
    ]

KEY_DECREASE = [
    0b00000,
    0b00000,
    0b11111,    
    0b01110,
    0b00100,
    0b00000,
    0b00000,
    0b00000
    ]




def test_main():
    #Test function for verifying basic functionality
    print("Running test_main")
    i2c = I2C(0, sda=machine.Pin(20), scl=machine.Pin(21), freq=400000)
    lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
    
    custom_char = "°⏴⏵⏶⏷"
    
    """
    custom_str = ""
    for i in range(len(custom_char)):
        char = custom_char[i]
        if char in utf8_char.CUSTOM_CHARACTERS:
            b_array = utf8_char.CUSTOM_CHARACTERS[char]
            lcd.custom_char(i,b_array)
            custom_str = custom_str + chr(i)
        i = i + 1
    """
    
    for char in custom_char:
        if char in utf8_char.CUSTOM_CHARACTERS:
            b_array = utf8_char.CUSTOM_CHARACTERS[char]
            lcd.def_special_char(char,b_array)
    
    """
    lcd.custom_char(0x00, degreeSymbol)
    lcd.custom_char(0x01, reverseBack)
    lcd.custom_char(0x02, forwardNextPlay)
    lcd.custom_char(0x03, KEY_INCREASE)
    lcd.custom_char(0x04, KEY_DECREASE)
    """
    
    # lcd.putstr("It Works!" + custom_str)  #+custom_char)
    lcd.putstr("It Works!" + custom_char) 
    
    utime.sleep(2)

    print("Filling display, "+str(I2C_NUM_ROWS) + ",  "+ str(I2C_NUM_COLS))
    
    i = 32
    row = 0
    col = 0
    lcd.clear()
    string = ""
    while i < 256:
        i += 1
        col += 1
        if col >= I2C_NUM_COLS:
            print("printing string: " + string)
            lcd.move_to(0,row)
            lcd.putstr(string)
            col = 0
            
            row += 1
            if row >= I2C_NUM_ROWS:
                print("sleep 4 sec")
                utime.sleep(4)
                lcd.clear()
                lcd.move_to(0,0)
                lcd.putstr(string)
                row = 0
                
            string = ""
            
        string += chr(i)

                

    
def more():
    utime.sleep(2)
    lcd.clear()
    count = 0


    while True:
        lcd.clear()
        time = utime.localtime()
        lcd.putstr("{year:>04d}/{month:>02d}/{day:>02d}\n {HH:>02d}:{MM:>02d}:{SS:>02d}".format(
            year=time[0], month=time[1], day=time[2],
            HH=time[3], MM=time[4], SS=time[5]))
        
        """
        lcd.putstr("{year:>04d}/{month:>02d}/{day:>02d}".format(
            year=time[0], month=time[1], day=time[2]))
        lcd.move_to(0,1)
        lcd.putstr("{HH:>02d}:{MM:>02d}:{SS:>02d}".format(
            HH=time[3], MM=time[4], SS=time[5]))
        """
        
        if count % 10 == 0:
            print("Turning cursor on")
            lcd.show_cursor()
        if count % 10 == 1:
            print("Turning cursor off")
            lcd.hide_cursor()
            
        if count % 10 == 2:
            print("Turning blink cursor on")
            lcd.blink_cursor_on()
        if count % 10 == 3:
            print("Turning blink cursor off")
            lcd.blink_cursor_off()                    
        if count % 10 == 4:
            print("Turning backlight off")
            lcd.backlight_off()
            

        if count % 10 == 5:
            print("Turning backlight on")
            lcd.backlight_on()
        if count % 10 == 6:
            print("Turning display off")
            lcd.display_off()
        if count % 10 == 7:
            print("Turning display on")
            lcd.display_on()
            

        if count % 10 == 8:
            print("Filling display, "+str(I2C_NUM_ROWS) + ",  "+ str(I2C_NUM_COLS))
            lcd.clear()
            string = ""
            for x in range(33, 33+I2C_NUM_ROWS*I2C_NUM_COLS):
                string += chr(x)
            lcd.putstr(string)
            
        

        count += 1
        utime.sleep(2)

#if __name__ == "__main__":
test_main()
