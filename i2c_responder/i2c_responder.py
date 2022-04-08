from machine import mem32

import sys
import uasyncio
from i2c_responder_base import I2CResponderBase

import calc_icmpv6_chksum
import queue

from micropython import const

_SEND_AVAILABLE = "sa"
_RECEIVE_AVAILABLE  = "ra"


_BLK_MSG_LENGTH_ACK_OK         = const(127 + 1)
_BLK_MSG_LENGTH_ACK_ERR_RESEND = const(127 + 2)
_BLK_MSG_LENGTH_ACK_ERR_CANCEL = const(127 + 3)

_BLK_MSG_CHKSUM_OKAY           = const(127 + 4)
_BLK_MSG_CHKSUM_ERR_RESENDING  = const(127 + 5)
_BLK_MSG_CHKSUM_ERR_CANCEL     = const(127 + 6)

class I2CResponder(I2CResponderBase):
    """
        Implementation of a (polled) Raspberry Pico I2C Responder.

        Subclass of the original I2CResponder class which has been renamed
        I2CReponderBase. See that class for more info.
                
        This new version I2CResponder implments a protocol which both Controller and Responder must adhere to
        in order to send longer messages.
        
        Created: March 30, 2022  By: D. Garrett
        
    """
    VERSION = "3.0.1"

    def __init__(self, i2c_device_id=0, sda_gpio=0, scl_gpio=1, responder_address=0x41,
                 q_in_size=30, q_out_size=30, trace=False):
        """Initialize.

        Args:
            i2c_device_id (int, optional): The internal Pico I2C device to use (0 or 1).
            sda_gpio (int, optional): The gpio number of the pin to use for SDA.
            scl_gpio (int, optional): The gpio number of the pin to use for SCL.
            responder_address (int, required): The I2C address to assign to this Responder.
        """

        super().__init__(i2c_device_id=i2c_device_id, sda_gpio=sda_gpio,
                         scl_gpio=scl_gpio, responder_address=responder_address)
        
        self.buff = bytearray(1024)
        self.buff_2 = bytearray(2)
        self.q_in = queue.Queue(q_in_size)
        self.q_out = queue.Queue(q_out_size)
        
        self.resend_cnt = 0
        self.failed_cnt = 0
        
        if trace:
            self.trace = self.print_trace
        else:
            self.trace = self.no_trace


    # Poll for send or receive requests from the I2C controller
    #
    # I2C Controller send requests will check the q_in for input.
    # If q_in has a message, it will be sent to the Controller.
    # If no q_in message, return a zero length response.
    #
    # Receive requests will read and then place a message on q_out.
    #
    # Note that this function never returns. Therefore it should be started
    # using
    #
    #      i2c_resp = I2CResponder(...)
    #      uasyncio.create_task(i2c_resp.poll_snd_rcv())
    #
    # Caller should then perform checks of i2c.q_out 
    # and write messages to be sent to i2c.q_in 
    #
    async def poll_snd_rcv(self):
        
        while True:
            
            # check first to see if I2C Controller is polling for input
            if self.read_is_pending():
                if self.q_in.empty():
                    await self.send_msg("")
                else:
                    msg = (await self.q_in.get())
                    await self.send_msg(msg)
                    
            # check to see if I2C Controller is waiting to send us a message
            if self.write_data_is_available():
                msg = (await self.rcv_msg())
                
                # Make sure we don't wait for a queue put.
                # If queue full, just silently discard input so we
                # don't hang the Controller.
                if (len(msg) > 0) and (not self.q_out.full()):
                    # TODO: catch error just in case?
                    # Impossible if we are only task putting msg in queue?
                    await self.q_out.put(msg)
                    
            await uasyncio.sleep_ms(0) 
                    
                
    """ ************************************************
        Receive a variable length message
        up to length of buffer.
    ************************************************ """ 
    async def rcv_msg(self):
        
        msg_len = await self.rcv_msg_length()
        
        if msg_len == 0:
            return ""
        
        if msg_len > len(self.buff):
            msg_len = len(self.buff)
        
        # now receive the actual message
        bytes_remain = msg_len
        offs = 0
        while bytes_remain > 0:
            
            # Read a block of data 
            self.buff_2[0] =_BLK_MSG_CHKSUM_ERR_RESENDING
            while self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_RESENDING:
                # receive n_bytes into buffer at offset offs
                n_bytes = await self.rcv_bytes(self.buff,offs,bytes_remain)
                
                # if 0 bytes received, something's wrong
                if n_bytes == 0:
                    self.trace("r03")
                
                # send back checksum
                cs = calc_icmpv6_chksum.calc_icmpv6_chksum(self.buff[offs:offs+n_bytes])
                self.buff_2[0:2] = bytearray(cs.to_bytes(2,sys.byteorder))
                if (await self.snd_bytes(self.buff_2,0,2)) != 2:
                    self.trace("s02")
            
                # receive checksum response
                if await self.rcv_bytes(self.buff_2,0,2) < 2:
                    self.trace("r04")
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
            
                # if chksum error, print
                if self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_RESENDING:
                    self.trace("rs02")
                
            # checksum error after n retries - return empty string
            if self.buff_2[0] != _BLK_MSG_CHKSUM_OKAY:
                self.trace("cs01")
                return ""
            
            # checksum okay
            # decrement number of bytes remaining and increment offset
            offs = offs + n_bytes
            bytes_remain = bytes_remain - n_bytes
               
        # return received string 
        return self.buff[0:msg_len].decode('utf8')
            

    # receive a 2 byte length
    async def rcv_msg_length(self):
        self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
        
        while self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND:
        
            # didn't receive 2 bytes before Controller requested a send
            if (await self.rcv_bytes(self.buff_2,0,2)) != 2:
                self.trace("r01")
                self.buff_2[0] = 0x00
                self.buff_2[1] = 0x00
            
            i = int.from_bytes(bytes(self.buff_2),sys.byteorder)              
                
            
            # echo length of message
            # first - flush any data Controller has sent us
            # not sure why it happens, but controller sometimes
            # seems to think we sent something already.
            # This was greatly reduced by having Controller pause
            # 2ms after sending length.
            ra = await self.await_send_rcv_avail()
            if ra == _RECEIVE_AVAILABLE:
                n = await self.rcv_bytes(self.buff,0,1000)
                self.trace("xtra" + str(n) )
            
            n = await self.snd_bytes(self.buff_2,0,2)
            if n != 2:
                self.trace("s01")

            # receive ack length okay or resend or cancel
            # self.await_send_rcv_avail()
            if (await self.rcv_bytes(self.buff_2,0,2)) < 1:
                self.trace("r02")
                self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND
                
            if self.buff_2[0] == _BLK_MSG_LENGTH_ACK_OK:
                return i
            
            self.trace("rs01")
            
        # not ack msg length okay or resend
        # cancelling send
        self.trace("cx01")
        return 0
    
    
    """ ************************************************
        Send a variable length message
    ************************************************ """ 

    async def send_msg(self, msg):
        
        # send length of message
        # UTF8 may have multibyte characters
        buff = bytearray(msg.encode('utf8'))
        
        await self.snd_msg_length(len(buff))
        if self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_CANCEL:
            return False
        
        # send message in 16 byte blocks
        # with checksum after each block
        msg_len        = len(buff)
        offs           = 0
        bytes_remain   = msg_len
        
        while bytes_remain > 0:
            
            n = (await self.send_block(buff,offs,bytes_remain))
            
            if self.buff_2[0] != _BLK_MSG_CHKSUM_OKAY:
                bytes_remain = 0
            else:
                bytes_remain = bytes_remain - n
                offs = offs + n
                
        
        if self.buff_2[0] == _BLK_MSG_CHKSUM_OKAY:
            return True
        
        return False            
            
        

    # Send message length and receive ack from Controller.
    # Will retry send 8 times, leaving final result in self.buff_2[0]
    async def snd_msg_length(self,length):
        
        # until send of length is okay
        # or give up resending
        self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
        retry_cnt = 8
        
        while self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND:
        
            # send 2 byte length
            self.buff_2[0:2] = length.to_bytes(2,sys.byteorder)
            n = await self.snd_bytes(self.buff_2,0,2)
            if n != 2:
                self.trace("sl10")
            
            # didn't receive 2 bytes before Controller requested a send
            if (await self.rcv_bytes(self.buff_2,0,2)) != 2:
                self.trace("sl11")
                self.buff_2[0] = 0x00
                self.buff_2[1] = 0x00
            
            i = int.from_bytes(bytes(self.buff_2),sys.byteorder)              
        
            # length okay?
            if i == length:
                self.buff_2[0] = _BLK_MSG_LENGTH_ACK_OK
            else:
                retry_cnt = retry_cnt - 1
                if retry_cnt > 0:
                    self.trace("sl12")
                    self.resend_cnt = self.resend_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_RESEND
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_LENGTH_ACK_ERR_CANCEL
            
            # send ack
            self.buff_2[1] = self.buff_2[0]
            n = await self.snd_bytes(self.buff_2,0,2)
            if n != 2:
                self.trace("sl13")

    # Send a given number of bytes from buff
    # starting at offs.
    # Responder should respond with a checksum after every block.
    # If checksum wrong, retransmit the block.
    # After 8 retransmits, cancel the send.
    async def send_block(self,buff,offs,send_cnt):
        
        # until send of block is okay
        # or give up resending
        self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
        retry_cnt = 8
        n = 0
        
        buff2 = bytearray(16)
        
        while self.buff_2[0] == _BLK_MSG_CHKSUM_ERR_RESENDING:
        
            # send as many bytes as the controller will accept
            
            # TEMP: limit to 16 bytes
            s_cnt = 16
            if send_cnt < s_cnt:
                s_cnt = send_cnt
                
            n = (await self.snd_bytes(buff,offs,send_cnt))
            
            # receive 2 byte checksum from Responder            
            r11 = await self.rcv_bytes(self.buff_2,0,2)
            if r11 != 2:
                self.trace("sb11-")
                self.trace(str(r11))
                self.buff_2[0] = 0x00
                self.buff_2[1] = 0x00
                
            i = int.from_bytes(self.buff_2,sys.byteorder)
            
            cs = calc_icmpv6_chksum.calc_icmpv6_chksum(buff[offs:offs+n]) 
        
            # checksum okay?
            if i == cs:
                self.buff_2[0] = _BLK_MSG_CHKSUM_OKAY
            else:
                retry_cnt = retry_cnt - 1
                if retry_cnt > 0:
                    self.resend_cnt = self.resend_cnt + 1
                    self.trace("sb12")
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_RESENDING
                else:
                    self.failed_cnt = self.failed_cnt + 1
                    self.buff_2[0] = _BLK_MSG_CHKSUM_ERR_CANCEL
            
            # send ack
            self.buff_2[1] = self.buff_2[0]               
            m = await self.snd_bytes(self.buff_2,0,2)
            if m != 2:
                self.trace("sb13")
            
        return n

    """ ************************************************
        Common routines used by both send and receive
    ************************************************ """ 
        
    #
    # Receive up to n_bytes of data into buff
    # starting at offset.
    #
    # Return number of bytes actually received
    # before requested number of bytes was read
    # or a SEND_AVAILABLE request was received.
    #
    async def rcv_bytes(self,buff,offs,n_bytes):
        for i in range(n_bytes):
            rw = await self.await_send_rcv_avail()
            if rw != _RECEIVE_AVAILABLE:
                return i
            
            # discard anything beyond end of buffer
            if offs > len(buff):
                b = (mem32[self.i2c_base | self.IC_DATA_CMD] & 0xFF)
            buff[offs] = (mem32[self.i2c_base | self.IC_DATA_CMD] & 0xFF)
            offs = offs + 1
        
        return n_bytes
                    
    #
    # Send up to n_bytes of data from buff
    # starting at offset.
    #
    # Return number of bytes actually sent
    # before requested number of bytes was sent
    # or a _RECEIVE_AVAILABLE request was received.
    #
    async def snd_bytes(self,buff,offs,n_bytes):            
        for i in range(n_bytes):
            rw = await self.await_send_rcv_avail()
            if rw != _SEND_AVAILABLE:
                return i
            self.put_read_data(buff[offs])
            offs = offs + 1
            
        return n_bytes
                    
    # loop until we get a write avail or read requested.
    # Return either _RECEIVE_AVAILABLE, if Controller is ready to send data
    # or _SEND_AVAILABLE if Controller is ready receive data
    async def await_send_rcv_avail(self):
        while True:
            if self.write_data_is_available():
                return _RECEIVE_AVAILABLE
            if self.read_is_pending():
                return _SEND_AVAILABLE
            
            await uasyncio.sleep_ms(0)
        
    def print_trace(self,s,end=" "):
        print(s,end=end)
        
    def no_trace(self,s,end=" "):
        pass
