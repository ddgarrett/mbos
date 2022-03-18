from machine import Pin, I2C
import time
import _thread
import sys

class I2cController:
    
    """
        I2C Controller Class.
        Implements Logic for Controllers on an I2C bus
        to send "larger" amounts of data across the line.
        
        On both sends and receives expects the first four bytes
        to be an integer defining the length of the remaining data.
        That data is then sent in blocks of up to 16 bytes.
        
        The first block, the one containing the four byte integer,
        also contains up to the first 12 bytes of the message.
        
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
        
    """
        Scan I2C network to find any IC2 Responders.
    """
    def scan(self):
        return self.i2c.scan()
    
    """
        Send a message in 16 byte or less blocks.
        First four bytes of the first block is the number of bytes
        remaining in the message.
        
        addr = address of the I2C device to send the message to
        msg  = the UTF-8 encoded string to send
    """
    def send_msg(self, addr, msg):
        
        buffer = bytearray([0x00]*16)
        rem_bytes = len(msg)
        if rem_bytes == 0:
            return
        
        # add length of message to output
        buffer[0:4] = bytearray(rem_bytes.to_bytes(4,sys.byteorder))
        if rem_bytes <= 12:
            # can send remainder of message with one xmit
            buffer[4:rem_bytes+4] = self.string_to_bytes(msg)
            self.send_block(addr,buffer[0:rem_bytes+4])
            return 

        # add first 12 bytes of message to buffer and send
        buffer[4:16] = self.string_to_bytes(msg[0:12])
        self.send_block(addr,buffer[0:16])
        msg_pos = 12
        rem_bytes = rem_bytes - 12
        
        while rem_bytes > 0:
            if rem_bytes <= 16:
                self.send_block(addr,self.string_to_bytes(msg[msg_pos:]))
                return
            
            self.send_block(addr,self.string_to_bytes(msg[msg_pos:msg_pos+16]))
            msg_pos = msg_pos + 16
            rem_bytes = rem_bytes - 16
            
    """
        Send a block of up to 16 bytes of data
    """
    def send_block(self,addr,block):
        self.i2c.writeto(addr, block)
        
        """
        for value in buffer_out:
            # loop (polling) until the Controller issues an I2C READ.
            while not self.read_is_pending():
                pass
            # self.put_read_data(value)
        """

    # read a message sent by a responders
    # and return to caller
    def read_msg(self, i2c_controller):
        # read first block containing length of message
        data = self.i2c_controller.readfrom(RESPONDER_ADDRESS, 4)
        msg_len = bytes_to_int(data)
        
        blk_len = 12 # remaining bytes to read from first block
        if msg_len < blk_len:
            blk_len = msg_len
            
        if blk_len > 0 :
            data = self.i2c_controller.readfrom(RESPONDER_ADDRESS, blk_len)
            msg = bytes_to_string(data)
            
        msg_len = msg_len - 12
        
        # read 16 byte blocks until the message is completely received
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
