 
from machine import Pin, I2C
from time import sleep
import sys
from i2c_controller import I2cController
import uasyncio

I2C_CHANNEL = 0
I2C_SCL_PIN = 21
I2C_SDA_PIN = 20

            
MSG_SIZE = 15

"""
i2c = I2C(I2C_CHANNEL, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100_000) 
addr = 0x09 # i2c.scan()[0]

#i2c.writeto(addr, 'Hi from Pi')
# i2c.writeto(addr, 'Hi from Pi    xx - and longer yet')
msg = "just a test"
msg_len  = len(msg)
buffer = bytearray([0x00]*16)
buffer[0:4] = bytearray(msg_len.to_bytes(4,sys.byteorder))
buffer[4:msg_len+4] = bytearray(msg.encode())
i2c.writeto(addr, buffer[0:msg_len+4])
# i2c.writeto(addr, buffer[0:4])
# i2c.writeto(addr, msg)

print("sent " + str(msg_len))
"""

"""
sleep(0.1)
a = i2c.readfrom(addr, MSG_SIZE)
print(a.decode())

print("done")
"""

def format_hex(_object):
    # Format a value or list of values as 2 digit hex.
    try:
        values_hex = [to_hex(value) for value in _object]
        return '[{}]'.format(', '.join(values_hex))
    except TypeError:
        # The object is a single value
        return to_hex(_object)
    
def to_hex(value):
    return '0x{:02X}'.format(value)
    

async def main():

    # for send long data
    controller = I2cController(i2c_channel=I2C_CHANNEL,
                              scl_pin=I2C_SCL_PIN,sda_pin=I2C_SDA_PIN )

    i2c = controller.i2c
    
    # scan I2C bus
    responder_addresses = controller.scan()
    print('I2C scan found: ' + format_hex(responder_addresses))
     
    addr = 0x09 # i2c.scan()[0]


    # send data
    await controller.send_msg(addr,"just a test")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test2")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test with longer message")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test with a really really really long message and even longer longer longer yet!")
    print(await controller.rcv_msg(addr))


uasyncio.run(main())

