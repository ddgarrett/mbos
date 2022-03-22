"""

    I2CResponder Test Application.
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
    
    # Check for Controller sending data
    # or requesting data
    while True:
        
        # is controller waiting for us to send data?
        while i2c_responder.read_is_pending():
            # send the last message received
            # last_msg = "pico2 rcvd: " + last_msg
            print("sending msg: " + last_msg)
            await i2c_responder.send_msg(last_msg)
            last_msg = ""
            
        # is controller trying to send us some data?
        while i2c_responder.write_data_is_available():
            last_msg = await i2c_responder.rcv_msg()
            print("rcvd msg( ",end="")
            print(len(last_msg),end="")
            print(") : " + last_msg )
            
        await uasyncio.sleep_ms(0)
        

if __name__ == "__main__":
    uasyncio.run(main())
    # main()
