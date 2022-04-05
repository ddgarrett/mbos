"""

    I2CResponder Test Application.
    
    Test receives from the service_i2c_controller
  
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


"""
RESPONDER_I2C_DEVICE_ID = 1
RESPONDER_ADDRESS = 0x41
GPIO_RESPONDER_SDA = 14
GPIO_RESPONDER_SCL = 15
"""

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
    
    # start I2C Responder Task
    uasyncio.create_task(i2c_responder.poll_snd_rcv())
    q_out = i2c_responder.q_out
    
    print("awaiting I2C data:")
    
    # Check i2c responder output q
    print("rcv: ",end="")
    rcnt = 0
    while True:
        
        if not q_out.empty():
            msg = await q_out.get()
            rcnt = rcnt + 1
            print(rcnt,end=" ")
            
            # print("i2c state (write/read): ",end="")
            # print(i2c_responder.write_data_is_available(),end=" ")
            # print(i2c_responder.read_is_pending())
            
        await uasyncio.sleep_ms(0)
        

        

if __name__ == "__main__":
    uasyncio.run(main())
    # main()
