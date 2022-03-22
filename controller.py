"""
    Start services asynchronously then check for service output messages.
    Route output messages to the appropriate input queue.
    Wait 0 milliseconds each loop to allow other coroutines opportunity to execute.
    
    For now starts all of the services in the parms file.
    
    Eventually want to:
    1. ONLY have definitions for local services and responder addresses
    2. poll responders to determine services running under them
    
    Services are defined in the file: core_0_services.json
    
"""

import uasyncio
from xmit_message import XmitMsg
import gc

async def main(parms):
    
    # Create svc_lookup, a dictionary of Services
    # where the servcie can be looked up by name
    print("ctrl: creating lookup list of Services")
    svc_lookup = {}
    defaults = parms["defaults"]
    for svc_parms in parms["services"]:
        print("... "+svc_parms['name']) # show name of service being started
        svc_parms["defaults"] = defaults  # every service has access to defaults
        module = __import__(svc_parms['module'])
        svc_lookup[svc_parms['name']] = module.ModuleService(svc_parms)
        
    print("ctrl: starting services")
    for key, svc in svc_lookup.items():
        uasyncio.create_task(svc.run())
    
    q_log = svc_lookup['log'].get_input_queue()
    await q_log.put(XmitMsg("ctrl","log","checking queues"))
    
    # json parm: should we log to and from for all messages?
    log_xmit = ("log_xmit" in parms) and (parms["log_xmit"] == True)
    
    # controller service who does polling of output queues
    controller_name = parms["controller"]
    controller_svc = svc_lookup[controller_name]
    
    pass_cnt = 5
    
    while True:
        
        # msg_passed true if a message is passed from one service to another
        msg_passed = await controller_svc.poll_output_queues(svc_lookup, log_xmit)      
        
        if msg_passed:
            pass_cnt -= 1
            if pass_cnt <= 0:
                pass_cnt = 5
                # await q_log.put(XmitMsg("controller","log","doing gc.collect()"))
                gc.collect()
            
        # allow co-routines to execute
        await uasyncio.sleep_ms(0)
        
