from machine import Pin, I2C
import utime

# import ds1307


"""
    Poll I2C to determine available devices.

"""

I2C_FREQUENCY = 100_000

i2c_parm = [
    [0, 100_000, 20, 21],
    [1, 400_000, 14, 15]  
]

"""
CONTROLLER_I2C_DEVICE_ID = 0
GPIO_CONTROLLER_SCL = 21
GPIO_CONTROLLER_SDA = 20
"""


CONTROLLER_I2C_DEVICE_ID = 1
GPIO_CONTROLLER_SCL = 15
GPIO_CONTROLLER_SDA = 14


"""
i2c_controller = I2C(
    CONTROLLER_I2C_DEVICE_ID,
    scl=Pin(GPIO_CONTROLLER_SCL),
    sda=Pin(GPIO_CONTROLLER_SDA),
    freq=I2C_FREQUENCY,
)
"""


def to_hex(value):
    return '0x{:02X}'.format(value)

def format_hex(_object):
    """Format a value or list of values as 2 digit hex."""
    try:
        values_hex = [to_hex(value) for value in _object]
        return '[{}]'.format(', '.join(values_hex))
    except TypeError:
        # The object is a single value
        return to_hex(_object)
    

# -----------------
# Demonstrate that the Responder is responding at its assigned I2C address.
# -----------------
print('Scanning I2C Bus for Responders...')

for p in i2c_parm:
    i2c = I2C(p[0], freq=p[1], sda=Pin(p[2]), scl=Pin(p[3]))
    print("\nscanning bus {}".format(p[0]))
    resp = i2c.scan()
    print("    Addresses found: {}".format(resp))

    
"""

ticks_start = utime.ticks_us()

resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()
resp_addr = i2c_controller.scan()

diff = (utime.ticks_us() - ticks_start)/10
"""

"""
print('I2C Addresses of Responders found: ' , end='')
print(resp_addr, end='')
print(' in {0:,.0f} μsec'.format(diff))

# arg... this shows 18,625 micro seconds, or 18.625ms per scan
# so we can't do this every loop
# alternative - start a separate thread and check it every so often to see if it is hung?


# print('I2C Addresses of Responders found: ' + format_hex(resp_addr))
print()


# rtc_addr = 0x68

# x = input("Year : ")

# print("you said: " + x)

"""




