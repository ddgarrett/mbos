"""

    I2CResponder Test Application.
    
    Test receives from the service_i2c_controller
                          I                                                 I
"""

# Standard Library
from machine import Pin, I2C

import uasyncio

# Local
from i2c_responder import I2CResponder

I2C_FREQUENCY = 100_000

RESPONDER_I2C_DEVICE_ID = 0
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 20
GPIO_RESPONDER_SCL = 21

async def main():


    
    # -----------------
    # Initialize Responder and Controller
    # -----------------
    i2c_responder = I2CResponder(
        RESPONDER_I2C_DEVICE_ID, sda_gpio=GPIO_RESPONDER_SDA, scl_gpio=GPIO_RESPONDER_SCL,
        responder_address=RESPONDER_ADDRESS
    )
    
    print('Testing I2CResponder v' + i2c_responder.VERSION)

    last_msg = ""
    
    awaiting_io_printed = False
    
    # Check for Controller sending data
    # or requesting data
    while True:
        
        # is controller waiting for us to send data?
        while i2c_responder.read_is_pending():
            if len(last_msg) > 0:
                print("snd msg (",end="")
                print(len(last_msg),end="")
                print("): " + last_msg)
                
            # reply even if last msg was empty string
            # echo last msg
            await i2c_responder.send_msg(last_msg)
            last_msg = ""
            print(".",end="")
 
            
            # don't echo last xmit
            # await i2c_responder.send_msg("")
            
        # is controller trying to send us some data?
        while i2c_responder.write_data_is_available():
            print("rcv data...")
            last_msg = await i2c_responder.rcv_msg()
            print("rcv msg (",end="")
            print(len(last_msg),end="")
            print("): " + last_msg )
            

            
        await uasyncio.sleep_ms(0)
        
        if last_msg == "" and not awaiting_io_printed:
            print("awaiting io")
            awaiting_io_printed = True
        

if __name__ == "__main__":
    uasyncio.run(main())
    # main()
