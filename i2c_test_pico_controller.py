 
from machine import Pin, I2C
import utime
import sys
from i2c_controller import I2cController
import uasyncio

from xmit_message import XmitMsg

I2C_CHANNEL = 0
I2C_SCL_PIN = 21
I2C_SDA_PIN = 20

            
MSG_SIZE = 15

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

    # i2c = controller.i2c
    
    # scan I2C bus
    responder_addresses = controller.scan()
    print('I2C scan found: ' + format_hex(responder_addresses))
     
    # addr = 0x09 # i2c.scan()[0]  # uno r3 address
    addr = 0x41


    """
    # send data
    await controller.send_msg(addr,"just a test")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test2")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test with longer message")
    print(await controller.rcv_msg(addr))

    await controller.send_msg(addr,"just a test with a really really really long message and even longer longer longer yet!")
    print(await controller.rcv_msg(addr))
    """
    
    # Test xmit wrap and unwrap
    
    # NOTE: having problem with utf8 encoding?
    
    # xmit_msg = """["temp_humid", "lcd", "<class 'XmitLcd'>", [{"cursor": [8, 0]}, {"msg": " 71.7°F"}, {"cursor": [12, 1]}, {"msg": "46%"}]]"""
    xmit_msg = """["temp_humid", "lcd", "<class 'XmitLcd'>", ["clear", {"msg": "⏶ Temp:\n⏷ Humidity:"}]]"""
    
    print("sending msg")
    
    await controller.send_msg(addr,xmit_msg)
    
    print("receiving msg")
    
    msg = await controller.rcv_msg(addr)
    print("msg: " + msg)
    
    """
    if len(msg) > 0:
        print("creating new xmit")
        xmit = XmitMsg(msg=msg)
        xmit.unwrapMsg()
        print("new xmit: "+xmit.dumps())
        msg = xmit.get_msg()
        print(type(msg))
        print(msg)
    else:
        print("zero length msg received")
    """
    

    return
    # time round trip
    ticks_start = utime.ticks_us()
    
    print("sending msg 1")
    
    xmit_msg = """["temp_humid", "lcd", "<class 'XmitLcd'>", ["clear", {"msg": "⏶ Temp:\n⏷ Humidity:"}]]"""
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    print("sending msg 2")
    
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    print("sending msg 3")
    
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    print("sending msg 4")
    
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    print("sending msg 5")
    
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    print("sending msg 6")
    
    await controller.send_msg(addr,xmit_msg)
    await controller.rcv_msg(addr)
    
    ticks = (utime.ticks_us() - ticks_start)/6
    print(ticks)



uasyncio.run(main())

