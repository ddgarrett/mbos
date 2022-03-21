from machine import Pin, I2C
import time

# import ds1307


"""
    Poll I2C to determine available devices.

"""

I2C_FREQUENCY = 100000

CONTROLLER_I2C_DEVICE_ID = 0
GPIO_CONTROLLER_SCL = 21
GPIO_CONTROLLER_SDA = 20

i2c_controller = I2C(
    CONTROLLER_I2C_DEVICE_ID,
    scl=Pin(GPIO_CONTROLLER_SCL),
    sda=Pin(GPIO_CONTROLLER_SDA),
    freq=I2C_FREQUENCY,
)   


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
responder_addresses = i2c_controller.scan()
print('I2C Addresses of Responders found: ' + format_hex(responder_addresses))
print()

rtc_addr = 0x68

# x = input("Year : ")

# print("you said: " + x)




