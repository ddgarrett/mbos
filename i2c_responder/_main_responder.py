"""
    Boot up MBOS (Microcontroller Basic OS)
    
    Read parameter file to start up services on the Cores

    NOTE: currently only starts up one core.
"""

import ujson
import uasyncio

# read the paramter file
with open("core_0_responder.json") as f:
        parms = ujson.load(f)

# start main
main_name = parms["main"]
print("starting " + main_name)

main = __import__(main_name)
uasyncio.run(main.main(parms))
    

