from machine import Pin, I2C

import sys
import uasyncio
import gc

import calc_icmpv6_chksum
from micropython import const


_BLK_MSG_LENGTH_ACK_OK         = const(127 + 1)
_BLK_MSG_LENGTH_ACK_ERR_RESEND = const(127 + 2)
_BLK_MSG_LENGTH_ACK_ERR_CANCEL = const(127 + 3)

_BLK_MSG_CHKSUM_OKAY           = const(127 + 4)
_BLK_MSG_CHKSUM_ERR_RESENDING  = const(127 + 5)
_BLK_MSG_CHKSUM_ERR_CANCEL     = const(127 + 6)


class I2cController:
    
    """
        I2C Controller Class.
        Implements Logic for Controller on an I2C bus
        to send "larger" amounts of data across the line.
        
        On both sends and receives expects the first two bytes
        to be an integer defining the length of the remaining data.
        
        That data is then sent in blocks of up to 16 bytes.
        
        Parms:
            - i2c_device_id = I2C device ID, 0 or 1
            - sda_pin=
            - scl_pin=
            

    """
    
    VERSION = "0.1.0"
        
    # add ability to pass in an existing i2c controller
    # If specified, will use that instead of creating a new one
    def __init__(self, i2c_channel=0, scl_pin=1, sda_pin=0, i2c_freq=100_000, i2c=None):
        
        if i2c == None:
            self.i2c = I2C(
                i2c_channel,
                scl=Pin(scl_pin),
                sda=Pin(sda_pin),
                freq=i2c_freq
            )
        else:
            self.i2c = i2c
            
        self.buff_2  = bytearray(2)
        self.buff_16 = bytearray(16)
        self.buff    = bytearray(4096)
        
        self.send_cnt   = 0
        self.rcv_cnt    = 0
        self.resend_cnt = 0
        self.failed_cnt = 0
        

    # Scan I2C network to find any IC2 Responders.
    def scan(self):
        return self.i2c.scan()
    
    """ ************************************************
        Send a variable length message
    ************************************************ """ 

    # TODO: add await uasyncio.sleep_ms(0)
    # to allow other tasks to execute
    # while waiting for I2C io
    async def send_msg(self,addr,msg):
        # avoid garbage collection during a transmit?
        # gc.collect()
        
        self.send_cnt = self.send_cnt + 1 
        
        buff = bytearray(msg.encode("utf8"))
        
        # send and confirm message length
        await self.snd_msg_length(addr,len(buff))
        if self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_CANCEL:
            return False
        
        # send message in 16 byte blocks
        # with checksum after each block
        msg_len        = len(buff)
        offs           = 0
        bytes_remain   = msg_len
        
        # wait to give sender time to before first block sent
        await uasyncio.sleep_ms(1)
        
        while bytes_remain > 0:
            
            await uasyncio.sleep_ms(1)

            bytes_send = 16
            if bytes_remain < 16:
                bytes_send = bytes_remain
                
            await self.send_block(addr,buff,offs,bytes_send)
            
            if self.buff_2[0] != _BLK_MSG_CHKSUM_OKAY:
                bytes_remain = 0
            else:
                bytes_remain = bytes_remain - bytes_send
                offs = offs + bytes_send
                
        
        if self.buff_2[0] == _BLK_MSG_CHKSUM_OKAY:
            return True
        
        return False
        
        
    # Send message length and receive ack from Responder.
    # Will retry send 8 times, leaving final result in self.buff_2[0]
    async def snd_msg_length(self,addr,length):
        
        # until send of length is okay
        # or give up resending
        self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
        retry_cnt = 8
        
        while self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND:
        
            # send 2 byte length
            self.buff_2[0:2] = length.to_bytes(2,sys.byteorder)
            self.i2c.writeto(addr,self.buff_2)
            
            # receive echo of length from responder
            # wait to give sender time to send
            await uasyncio.sleep_ms(2)
            self.i2c.readfrom_into(addr,self.buff_2)
            i = int.from_bytes(self.buff_2,sys.byteorder)
        
            # length okay?
            if i == length:
                self.buff_2[0] = _BLK_MSG_LENGTH_ACK_OK
            else:
                retry_cnt = retry_cnt - 1
                if retry_cnt > 0:
                    self.resend_cnt = self.resend_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_CANCEL
            
            # send ack
            self.buff_2[1] = self.buff_2[0]
            self.i2c.writeto(addr,self.buff_2)
        

    # Send a given number of bytes from buff
    # starting at offs.
    # Responder should respond with a checksum after every block.
    # If checksum wrong, retransmit the block.
    # After 8 retransmits, cancel the send.
    async def send_block(self,addr,buff,offs,send_cnt):
        
        # until send of block is okay
        # or give up resending
        self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
        retry_cnt = 8
        i2c = self.i2c
        
        while self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_RESENDING:
        
            # send up to 16 bytes
            blk_size = 16
            if send_cnt < 16:
                blk_size = send_cnt
                
            i2c.writeto(addr,buff[offs:offs+blk_size])
            
            # receive 2 byte checksum from Responder
            i2c.readfrom_into(addr,self.buff_2)
            i = int.from_bytes(self.buff_2,sys.byteorder)
            
            cs = calc_icmpv6_chksum.calc_icmpv6_chksum(buff[offs:offs+blk_size]) 
        
            # checksum okay?
            if i == cs:
                self.buff_2[0] = _BLK_MSG_CHKSUM_OKAY
            else:
                retry_cnt = retry_cnt - 1
                if retry_cnt > 0:
                    self.resend_cnt = self.resend_cnt + 1
                    print("rt02 ",end="")
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_CANCEL
            
            # send ack
            self.buff_2[1] = self.buff_2[0]
            i2c.writeto(addr,self.buff_2)
            

    """ ************************************************
        Receive a variable length message
    ************************************************ """ 
    async def rcv_msg(self, addr):
        
        # gc.collect()
        
        msg_len = await self.rcv_msg_length(addr)
        
        if msg_len == 0:
            return ""
        
        self.rcv_cnt = self.rcv_cnt + 1
        
        blk_len = 16
        offs    = 0
        rem_cnt = msg_len
        
        # read block with up to 16 bytes until the message is completely received
        while (rem_cnt > 0):

            cnt  = blk_len

            if rem_cnt < blk_len:
                cnt = rem_cnt
                
            buff = await self.rcv_block(addr,cnt)
            
            if self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_CANCEL:
                self.failed_cnt = self.failed_cnt + 1
                return ""
            
            self.buff[offs:offs+cnt] = buff
            offs = offs + cnt
            rem_cnt = rem_cnt - cnt

            # Increase to give sender time to send?
            # await uasyncio.sleep_ms(0) # play nice with coroutines
            
        return self.buff[0:msg_len].decode('utf8')

    # receive a 2 byte length
    async def rcv_msg_length(self,addr):
        self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
        
        while self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND:
        
            # wait to give sender time to catch up before trying to read?
            await uasyncio.sleep_ms(1)
            
            # read length of message
            self.i2c.readfrom_into(addr,self.buff_2)
            msg_len = int.from_bytes(self.buff_2,sys.byteorder)
            
            # echo message length
            self.i2c.writeto(addr,self.buff_2)
            
            # read ack
            self.i2c.readfrom_into(addr,self.buff_2)
            
            if self.buff_2[0] == _BLK_MSG_LENGTH_ACK_OK:
                return msg_len
         
            self.resend_cnt = self.resend_cnt + 1
            
            # wait to give sender time to catch up before trying to read again?
            # await uasyncio.sleep_ms(1)
            
            
        # not ack msg length okay or resend
        # cancelling send
        self.failed_cnt = self.failed_cnt + 1
        
        return 0
        
    # Receive a block into buff.
    # Length of buff must be number of bytes to receive.
    # Send checksum after each block and
    # wait for responder to acknowledge.
    # Final ack is in buff_2.
    async def rcv_block(self,addr,blk_len):
        
        buff = bytearray(blk_len)
        self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
        
        while self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_RESENDING:
            
            # receive 16 byte block
            self.i2c.readfrom_into(addr,buff)
        
            # send back checksum
            cs = calc_icmpv6_chksum.calc_icmpv6_chksum(buff)
            self.buff_2[0:2] = cs.to_bytes(2,sys.byteorder)
            self.i2c.writeto(addr,self.buff_2)
            
            # receive ack
            self.i2c.readfrom_into(addr,self.buff_2)
            
            # increment every time but decrement at end if okay
            self.resend_cnt = self.resend_cnt + 1

        if self.buff_2[0] == _BLK_MSG_CHKSUM_OKAY:
            self.resend_cnt = self.resend_cnt - 1
            
        return buff
    

