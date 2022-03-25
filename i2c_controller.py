from machine import Pin, I2C
# import time
# import _thread
import sys
import uasyncio

class I2cController:
    
    """
        I2C Controller Class.
        Implements Logic for Controller on an I2C bus
        to send "larger" amounts of data across the line.
        
        On both sends and receives expects the first four bytes
        to be an integer defining the length of the remaining data.
        
        That data is then sent in blocks of up to 16 bytes.
        
        Parms:
            - i2c_device_id = I2C device ID, 0 or 1
            - sda_pin=
            - scl_pin=
            

    """
    
    VERSION = "0.0.1"
        
    def __init__(self, i2c_channel=0, scl_pin=1, sda_pin=0, i2c_freq=100_000):
        
        self.i2c = I2C(
            i2c_channel,
            scl=Pin(scl_pin),
            sda=Pin(sda_pin),
            freq=i2c_freq
        )
        

    # Scan I2C network to find any IC2 Responders.
    def scan(self):
        return self.i2c.scan()
    
    """
        Send a message in 16 byte or less blocks.
        
        First sends a single 4 byte block with length of message,
        then the remaining message in blocks of up to 16 bytes.
        
        addr = address of the I2C device to send the message to
        msg  = the UTF-8 encoded string to send
    """
    async def send_msg(self, addr, msg):
        
        buff = bytearray(msg.encode('utf8'))
        rem_bytes = len(buff)
        # writeblk = self.i2c.writeto  # slight performance boost

        # send message length to receiver
        buffer = bytearray(rem_bytes.to_bytes(4,sys.byteorder))
        self.i2c.writeto(addr, buffer)
        
        msg_pos = 0
        while rem_bytes > 0:
            if rem_bytes <= 16:
                self.i2c.writeto(addr,buff[msg_pos:])
                print("wrote ",end="")
                print(buff[msg_pos:])
            else:
                self.i2c.writeto(addr,buff[msg_pos:msg_pos+16])
                print("wrote ",end="")
                print(buff[msg_pos:msg_pos+16])
                msg_pos = msg_pos + 16
                
                
            rem_bytes = rem_bytes - 16
            
            # May be causing problems?
            # try waiting to give receiver time to receive?
            await uasyncio.sleep_ms(1)
            
            # await uasyncio.sleep_ms(0) # play nice with coroutines
            
    # read a message sent by a responders
    # and return to caller
    async def rcv_msg(self, addr):
        readblk = self.i2c.readfrom # slight performance boost
        
        # read first block containing length of message
        data = readblk(addr, 4)
        msg_len = int.from_bytes(data,sys.byteorder)


        # read 16 byte blocks until the message is completely received
        data = bytearray(b'')
        while (msg_len > 0):
            blk_len = 16
            if msg_len < blk_len:
                blk_len = msg_len
                
            blk = readblk(addr, blk_len)
            data = data +  blk
            msg_len = msg_len - len(blk)
            
            # Give sender time to send?
            await uasyncio.sleep_ms(1) # play nice with coroutines
            
        return bytearray(data).decode('utf8')

