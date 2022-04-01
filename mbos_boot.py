"""
    Boot up MBOS (Microcontroller Basic OS)
    
    Read parameter file to start up services on the Cores
    
    NOTE: currently only starts up one core.
"""

import ujson
import uasyncio

# read the paramter file
with open("core_0_services.json") as f:
        parms = ujson.load(f)

# start main
if "name" in parms:
    print("starting",parms["name"])
          
main_name = parms["main"]
print("starting " + main_name)

main = __import__(main_name)
uasyncio.run(main.main(parms))
    


