from machine import mem32
# import time
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

_TXN_CONTINUE                  = const(127+16)
_TXN_CANCEL                    = const(127+17)



class I2CResponder(I2CResponderBase):
    """Implementation of a (polled) Raspberry Pico I2C Responder.

        Subclass of the original I2CResponder class which has been renamed
        I2CReponderBase. See that class for more info.
                
        This new version I2CResponder implments a protocol which both Controller and Responder must adhere to
        in order to send longer messages.
        
        Created: March 30, 2022  By: D. Garrett
        
    
    """
    VERSION = "3.0.1"


    def __init__(self, i2c_device_id=0, sda_gpio=0, scl_gpio=1, responder_address=0x41,
                 q_in_size=30, q_out_size=30):
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
        
        self.trace = False


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
        
        q_in  = self.q_in
        q_out = self.q_out
        
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
                    
                
    """
        Receive a variable length message up to length of buffer.
    """
    async def rcv_msg(self):
        
        msg_len = await self.rcv_msg_length()
        
        if msg_len == 0:
            # print("msg_len 0")
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
                if await self.rcv_bytes(self.buff_2,0,1) != 1:
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
            # seems to think we sent something already
            ra = await self.await_send_rcv_avail()
            if ra == _RECEIVE_AVAILABLE:
                n = await self.rcv_bytes(self.buff,0,1000)
#                 print("(",end="")
#                 print(self.buff_2,end=" ")
#                 print(self.buff[0:n],end=" ")
#                 print(n,end=") ")
            
            n = await self.snd_bytes(self.buff_2,0,2)
            if n != 2:
                self.trace("s01")

            # receive ack length okay or resend or cancel
            # self.await_send_rcv_avail()
            if (await self.rcv_bytes(self.buff_2,0,1)) != 1:
                self.trace("r02")
                self.buff_2[0] == _BLK_MSG_LENGTH_ACK_ERR_RESEND
                
            # echo last ack?
            # n = await self.snd_bytes(self.buff_2,0,1)
            
            if self.buff_2[0] == _BLK_MSG_LENGTH_ACK_OK:
                return i
            
            self.trace("rs01")
            
        # not ack msg length okay or resend
        # cancelling send
        self.trace("cx01")
        return 0
        
        
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
        # await send available
        # while (await self.await_send_rcv_avail()) != _SEND_AVAILABLE:
        #    await uasyncio.sleep_ms(0)
            
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
        
    """
        Version 1 code

    """

                
    """
        Read a long message from the Controller.
        
        Send an acknowledgment to the Controller of
        if the receive was successful.
          
        If receive failed, retry up to 5 times, then send 2
        telling controller it was a permanent error and
        don't bother to resend.
        
        If failed receive, returns an empty string,
        else returns the string received.
    """
    
    """
    async def rcv_msg_v01(self):
        
        if not self.write_data_is_available():
            return ""
        
        retry = 8
        ok = False
        
        while not ok and retry > 0:
            b_array, ok = await self.rcv_block()
            
            retry = retry - 1
            
            if retry > 0:
                # Controller will resend if not okay
                await self.send_ack(int(ok))
                
                if not ok:
                       
                    print("receive error... ",end="")
                    print((5-retry))
                    print("received: ", end="")
                    print(b_array)

                    
                    # await uasyncio.sleep_ms(0)
            else:
                # permanent error - don't resend
                print("***** permanent receive error *****")
                await self.send_ack(2) 

        if ok:
            # don't try to decode invalid receive.
            # may result in decode error.
            return b_array.decode('utf8')
        else:
            return ""
    """
                    
    """
        Send a 2 byte int acknowledgement to the Controller of
        message received.
        1 = message received ok and checksum matched
        0 = message not received ok, resend
        2 = message not received ok, but don't resend
    """
    """
    async def send_ack(self, ok):
        b = bytearray(ok.to_bytes(2,sys.byteorder))
        await self.send_bytes(b)
    """
    
    """
        Receive a byte array data where the first two bytes
        of the input stream contain the msg length and the
        next two contain a checksum.
        
        Return a byte array of data and True/False for if the
        checksum matched.
    """
    """
    async def rcv_block(self):
        
        # read length of message and checksum
        data = self.get_write_data(max_size=4)
        n_bytes = int.from_bytes(bytes(data[0:2]),sys.byteorder)
        chksum = int.from_bytes(bytes(data[2:4]),sys.byteorder)
        
        
        print("rcv bytes: ",end="")
        print(n_bytes, end="")
        print(", checksum: ",end="")
        print(chksum)
        
        
        r = await self.rcv_bytes(n_bytes)

        # print("returning results")
        # r = bytearray(data)
        cs = calc_icmpv6_chksum.calc_icmpv6_chksum(r)
        
        # wait until all sent data is received
        # and controller issues a read for the ack
        while not self.read_is_pending():
            if self.write_data_is_available():
                self.get_write_data(max_size=16)
                
        
        return r, cs == chksum
    """   
        
    """
        Receive bytes in blocks of 16 bytes or less until
        n_bytes of data received or "times out".
        
        Here, "times out" means no bytes received
        for 50ms.
        
        Returns a list of bytes.
    """
    """
    async def rcv_bytes(self, rem_bytes):
       
        data = bytearray(rem_bytes)
        data_offset = 0
        wait_cnt = 0
        
        empty = []
        
        while rem_bytes > 0:
                
            if self.write_data_is_available():
                b = self.get_write_data(max_size=16)
            else:
                b = empty

            if len(b) == 0:
                print("+",end="")
                await uasyncio.sleep_ms(5)
                wait_cnt = wait_cnt + 1
                if wait_cnt > 50:
                    # time out receive - exit early
                    # print("i2c_responder.rcv_msg() tired of waiting, exiting before EOD")
                    return data[:data_offset] 
            else:
                wait_cnt = 0
                r_cnt = len(b)
                rem_bytes = rem_bytes - r_cnt
                
                for i in range(r_cnt):
                    data[data_offset] = b[i]
                    data_offset = data_offset + 1
                

                if rem_bytes > 0 and r_cnt != 16:
                    # received a short block
                    print("**** <16 bytes in block: ", end="")
                    print(len(b))
                    return data[:data_offset] 
                
                    
                
                print("v2 rcvd '", end="")
                print(bytearray(b),end="")
                print("' blk remain: ",end="")
                print(rem_bytes)
                
                
        return data
    """

    """
        Send a long message to the Controller
        16 bytes at a time.
        
        First send 4 byte length of message.
        Then send blocks of up to 16 bytes.
    """

    async def send_msg(self, msg):
        
        # send length of message
        # UTF8 may have multibyte characters
        buff = bytearray(msg.encode('utf8'))
        rem_bytes = len(buff)
        
        len_buff = bytearray(rem_bytes.to_bytes(4,sys.byteorder))
        await self.send_bytes(len_buff)
        
        # print("sending: " + str(len_buff))
        
        # send message
        msg_pos = 0
        
        # if controller no longer requesting input
        # stop sending data
        while rem_bytes > 0: # and self.read_is_pending():
            if rem_bytes <= 16:
                await self.send_bytes(buff[msg_pos:])
                return
            
            await self.send_bytes(buff[msg_pos:msg_pos+16])
            msg_pos += 16
            rem_bytes -= 16
            
    """
        Send a block bytes of up to 16 bytes of data
    """
    async def send_bytes(self,buffer_out):
        for value in buffer_out:
            # loop (polling) until the Controller issues an I2C READ.
            while not self.read_is_pending():
               await uasyncio.sleep_ms(0)
            
            # stop sending if controller no longer soliciting input
            # if not self.read_is_pending():
            #    return
            
            self.put_read_data(value)

    def trace(self,s,end=" "):
        if self.trace:
            print(s,end=end)
