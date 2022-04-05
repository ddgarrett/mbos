from machine import Pin, I2C
# import time
# import _thread
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
        
        On both sends and receives expects the first four bytes
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
            
        self.buff_2 = bytearray(2)
        
        self.resend_cnt = 0
        self.failed_cnt = 0
        

    # Scan I2C network to find any IC2 Responders.
    def scan(self):
        return self.i2c.scan()
    
    # TODO: add await uasyncio.sleep_ms(0)
    # to allow other tasks to execute
    # while waiting for I2C io
    async def send_msg(self,addr,msg):
        # avoid garbage collection during a transmit?
        gc.collect()
        
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
        
        while bytes_remain > 0:
            
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
        i2c = self.i2c
        
        while self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND:
        
            # send 2 byte length
            self.buff_2[0:2] = length.to_bytes(2,sys.byteorder)
            i2c.writeto(addr,self.buff_2)
            
            # receive echo of length from responder
            # print("rcvd length echo from responder: ",end="")
            i2c.readfrom_into(addr,self.buff_2)
            i = int.from_bytes(self.buff_2,sys.byteorder)
            # print(i)
        
            # length okay?
            if i == length:
                self.buff_2[0] = _BLK_MSG_LENGTH_ACK_OK
            else:
                retry_cnt = retry_cnt - 1
                if retry_cnt > 0:
                    # print("retry length ack")
                    self.resend_cnt = self.resend_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_CANCEL
            
            # send ack
            i2c.writeto(addr,self.buff_2[0:1])

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
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_CANCEL
            
            # send ack
            i2c.writeto(addr,self.buff_2[0:1])

    """
        Previous version of code below

    """
    
    """
        Send a message in 16 byte or less blocks.
        
        First sends a single 4 byte block with length of message,
        then the remaining message in blocks of up to 16 bytes.
        
        addr = address of the I2C device to send the message to
        msg  = the UTF-8 encoded string to send
    """
    async def send_msg_v1(self, addr, msg):
        
        # avoid garbage collection during a transmit?
        gc.collect()
        
        buff = bytearray(msg.encode('utf8'))
        # cs = calc_icmpv6_chksum.calc_icmpv6_chksum(buff)
        
        ack = 0
        
        # keep resending until receiver
        # receives ok or says not okay but
        # don't retransmit
        rexmit = False
        while ack == 0:  
        
            await self.send_bytes(addr, buff, cs)
        
            # receive 2 byte acknowledgement from Responder
            # 1 = ok, 0 = error, resend, 2 = error, no resend
            data = self.i2c.readfrom(addr, 2)
            ack = int.from_bytes(data,sys.byteorder)
            
            if ack == 0:
                if not rexmit:
                    print("* rexmit: ", end="")
                print("+",end="")
                rexmit = True
            elif ack == 2:
                print("*** requeue xmit?")
            else:
                if rexmit:
                    print("")
            
        
            # print("ack: ", end="")
            # print(ack)

        
        
    """
        Send a message in 16 byte or less blocks.
        
        First sends a single 4 byte block with a 2 byte length of message,
        and a 2 byte checksum then the remaining message
        in blocks of up to 16 bytes.
        
        addr = address of the I2C device to send the message to
        buff  = the byte array to send
    """
    async def send_bytes(self, addr, buff, checksum):

        rem_bytes = len(buff)
        # writeblk = self.i2c.writeto  # slight performance boost

        # send message length to receiver
        buffer = bytearray(rem_bytes.to_bytes(2,sys.byteorder))
        # self.i2c.writeto(addr, buffer)
        
        # send checksum
        buffer += bytearray(checksum.to_bytes(2,sys.byteorder))
        self.i2c.writeto(addr, buffer)
        
        """
        print("snd bytes: ",end="")
        print(rem_bytes, end="")
        print(", checksum: ",end="")
        print(checksum)
        """
        
        msg_pos = 0
        while rem_bytes > 0:
            if rem_bytes <= 16:
                self.i2c.writeto(addr,buff[msg_pos:])
                # print("wrote ",end="")
                # print(buff[msg_pos:])
            else:
                self.i2c.writeto(addr,buff[msg_pos:msg_pos+16])
                # print("wrote ",end="")
                # print(buff[msg_pos:msg_pos+16])
                msg_pos = msg_pos + 16
                
                
            rem_bytes = rem_bytes - 16
            
            # May be causing problems?
            # try waiting to give receiver time to receive?
            await uasyncio.sleep_ms(2)
            
            # await uasyncio.sleep_ms(0) # play nice with coroutines
            
    # read a message sent by a responders
    # and return to caller
    async def rcv_msg(self, addr):
        # readblk = self.i2c.readfrom # slight performance boost
        
        # read first block containing length of message
        data = self.i2c.readfrom(addr, 4)
        msg_len = int.from_bytes(data,sys.byteorder)

        # print("read msg len=",end="")
        # print(msg_len)
        
        # read 16 byte blocks until the message is completely received
        data = bytearray(b'')
        while (msg_len > 0):
            blk_len = 16
            if msg_len < blk_len:
                blk_len = msg_len
                
            blk = self.i2c.readfrom(addr, blk_len)
            data = data +  blk
            msg_len = msg_len - len(blk)
            
            # print("read: ",end="")
            # print(data,end="")
            # print(", remain: ",end="")
            # print(msg_len)
            
            # Give sender time to send?
            await uasyncio.sleep_ms(1) # play nice with coroutines
            
        return bytearray(data).decode('utf8')

