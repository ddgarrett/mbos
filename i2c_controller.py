from machine import Pin, I2C
import time
import _thread
import sys

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
    def send_msg(self, addr, msg):
        
        rem_bytes = len(msg)

        # send message length to receiver
        buffer = bytearray(rem_bytes.to_bytes(4,sys.byteorder))
        self.send_block(addr, buffer)
        
        msg_pos = 0
        while rem_bytes > 0:
            if rem_bytes <= 16:
                self.send_block(addr,self.msg[msg_pos:])
                return
            
            self.send_block(addr,self.msg[msg_pos:msg_pos+16])
            msg_pos = msg_pos + 16
            rem_bytes = rem_bytes - 16
            
    """
        Send a block of up to 16 bytes of data.
        Block can be a string or a byte array
    """
    def send_block(self,addr,block):
        if if type(block) is str:
            self.i2c.writeto(addr, string_to_bytes(block))
        else:
            self.i2c.writeto(addr, block)

    # read a message sent by a responders
    # and return to caller
    def read_msg(self, addr):
        # read first block containing length of message
        data = self.i2c_controller.readfrom(addr, 4)
        msg_len = bytes_to_int(data)
                
        # read 16 byte blocks until the message is completely received
        msg = ""
        while (msg_len > 0):
            blk_len = 16
            if msg_len < blk_len:
                blk_len = msg_len
                
            data = self.i2c_controller.readfrom(RESPONDER_ADDRESS, blk_len)
            msg = msg + bytes_to_string(data)
            msg_len = msg_len - 16
            
        return msg

    def string_to_bytes(self,a_string):
        return bytearray(a_string.encode())
    
    def bytes_to_string(self,byte_array):
        return byte_array.decode()
