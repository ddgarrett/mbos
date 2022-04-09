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
        responder_address=RESPONDER_ADDRESS, trace=True
    )
    
    print('Testing I2CResponder v' + i2c_responder.VERSION)

    last_msg = ""
    
    awaiting_io_printed = False
    
    # start I2C Responder Task
    uasyncio.create_task(i2c_responder.poll_snd_rcv())
    q_out = i2c_responder.q_out
    q_in  = i2c_responder.q_in
    
    print("awaiting I2C data:")
    
    # Check i2c responder output q
    print("rcv: ",end="")
    rcnt = 0
    scnt = 0
    while True:
        
        if not q_out.empty():
            msg = await q_out.get()
            rcnt = rcnt + 1
            
            # print("r{}".format(rcnt), end=" ")
            print("+",end="")
            
            """
            if len(msg) > 0:
                # resend the message
                resend =  msg
                scnt = scnt + 1
                # resend = "test a much much much much much longer send message"
                # print("sending :",resend)
                await q_in.put(resend)
                # print("s{}".format(scnt),end=" ")
            """
                
        await uasyncio.sleep_ms(0)
        

        

if __name__ == "__main__":
    uasyncio.run(main())
    # main()
