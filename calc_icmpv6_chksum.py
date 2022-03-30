from struct import unpack

def calc_icmpv6_chksum(packet):
    """Calculate the ICMPv6 checksum for a packet.

    :param packet: The packet bytes to checksum.
    :returns: The checksum integer.
    
    
    from: https://www.programcreek.com/python/?CodeExample=calculate+checksum
    """
    total = 0

    # Add up 16-bit words
    num_words = len(packet) // 2
    for chunk in unpack("!%sH" % num_words, packet[0:num_words * 2]):
        total += chunk

    # Add any left over byte
    if len(packet) % 2:
        total += packet[-1] << 8

    # Fold 32-bits into 16-bits
    total = (total >> 16) + (total & 0xffff)
    total += total >> 16
    return ~total + 0x10000 & 0xffff 