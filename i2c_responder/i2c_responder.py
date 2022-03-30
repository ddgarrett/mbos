from machine import mem32
# import time
import sys
import uasyncio
from i2c_responder_base import I2CResponderBase

import calc_icmpv6_chksum


class I2CResponder(I2CResponderBase):
    """Implementation of a (polled) Raspberry Pico I2C Responder.

        Subclass of the original I2CResponder class which has been renamed
        I2CReponderBase. See that class for more info.
                
        This new version I2CResponder implments a protocol which both Controller and Responder must adhere to
        in order to send longer messages.
        
        Created: March 30, 2022  By: D. Garrett
        
    
    """
    VERSION = "2.0.1"


    def __init__(self, i2c_device_id=0, sda_gpio=0, scl_gpio=1, responder_address=0x41):
        """Initialize.

        Args:
            i2c_device_id (int, optional): The internal Pico I2C device to use (0 or 1).
            sda_gpio (int, optional): The gpio number of the pin to use for SDA.
            scl_gpio (int, optional): The gpio number of the pin to use for SCL.
            responder_address (int, required): The I2C address to assign to this Responder.
        """

        super().__init__(i2c_device_id=i2c_device_id, sda_gpio=sda_gpio,
                         scl_gpio=scl_gpio, responder_address=responder_address)


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
    async def rcv_msg(self):
        
        if not self.write_data_is_available():
            return ""
        
        retry = 5
        ok = False
        
        while not ok and retry > 0:
            b_array, ok = await self.rcv_block()
            
            retry = retry - 1
            
            if retry > 0:
                # Controller will resend if not okay
                await self.send_ack(int(ok)) 
            else:
                # permanent error - don't resend
                await self.send_ack(2) 

        if ok:
            # don't try to decode invalid receive.
            # may result in decode error.
            return b_array.decode('utf8')
        else:
            return ""
        
    """
        Send a 2 byte int acknowledgement to the Controller of
        message received.
        1 = message received ok and checksum matched
        0 = message not received ok, resend
        2 = message not received ok, but don't resend
    """
    async def send_ack(self, ok):
        b = bytearray(ok.to_bytes(2,sys.byteorder))
        await self.send_bytes(b)

    """
        Receive a byte array data where the first two bytes
        of the input stream contain the msg length and the
        next two contain a checksum.
        
        Return a byte array of data and True/False for if the
        checksum matched.
    """
    async def rcv_block(self):
        
        # read length of message and checksum
        data = self.get_write_data(max_size=4)
        n_bytes = int.from_bytes(bytes(data[0:2]),sys.byteorder)
        chksum = int.from_bytes(bytes(data[2:4]),sys.byteorder)
        
        """
        print("rcv bytes: ",end="")
        print(rem_bytes, end="")
        print(", checksum: ",end="")
        print(chksum)
        """
        
        data = await self.rcv_bytes(n_bytes)

        # print("returning results")
        r = bytearray(data)
        cs = calc_icmpv6_chksum.calc_icmpv6_chksum(r) 
        return r, cs == chksum
        
        
    """
        Receive bytes in blocks of 16 bytes or less until
        n_bytes of data received or "times out".
        
        Here, "times out" means no bytes received
        for 50ms.
        
        Returns a list of bytes.
    """
    async def rcv_bytes(self, rem_bytes):
       
        data = []
        wait_cnt = 0
        while rem_bytes > 0:
            b = self.get_write_data(max_size=16)        

            
            if len(b) == 0:
                # print("+",end="")
                await uasyncio.sleep_ms(1)
                wait_cnt = wait_cnt + 1
                if wait_cnt > 50:
                    # time out receive - exit early
                    # print("i2c_responder.rcv_msg() tired of waiting, exiting before EOD")
                    return data   
            else:
                wait_cnt = 0
                r_cnt = len(b)
                data += b
                rem_bytes = rem_bytes - r_cnt

                if rem_bytes > 0 and r_cnt != 16:
                    # received a short block
                    print("**** <16 bytes in block: ", end="")
                    print(len(b))
                    
                """
                print("v2 rcvd '", end="")
                print(bytearray(b),end="")
                print("' blk remain: ",end="")
                print(rem_bytes)
                """
                
        return data

