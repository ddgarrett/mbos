
import calc_icmpv6_chksum
import sys


msg = '["temp_humid", "lcd", "<class XmitLcd>", [{"cursor": [8, 0]}, {"msg": " 61.6°F"}, {"cursor": [12, 1]}, {"msg": "56%"}]]'

b = bytearray(msg.encode('utf8'))

chks = calc_icmpv6_chksum.calc_icmpv6_chksum(b)

rem_bytes = len(b)

print(msg)
print(chks)
bm = bytearray(rem_bytes.to_bytes(2,sys.byteorder))
bs = bytearray(chks.to_bytes(2,sys.byteorder))



s = "msg len: {}, from bytes: {}, len:{}".format(rem_bytes,int.from_bytes(bm,sys.byteorder),len(bm))
print(s)

s = "chk sum: {}, from bytes: {}, len:{}".format(chks,int.from_bytes(bs,sys.byteorder),len(bs))
print(s)



