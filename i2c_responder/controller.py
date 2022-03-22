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
        
        # TODO: find out why gc.collect() causes DHT11 sensor to have errors.
        # Doing garbage collection too frequently seemed to cause problems for the DHT11 Service?
        # Doing it only if a message was actually passed reduced frequency of problem?
        # But, as we pass more messages, problem may reoccur?
        # In any case, if we're not passing messages we're not doing any work.
        # And if we're not doing any work, we shouldn't need to run the garbage collection?
        # **MAY** have been caused or made worse by connecting dth11 to 3.3v power instead of 5v?
        # Have switched to 5v power and haven't seen any errors?
        # Did have errors with 5v. Switched back to 3.3v and changed driver.
        # Driver minimum checking period was set to .2 sec instead of 1 sec.
        if msg_passed:
            pass_cnt -= 1
            if pass_cnt <= 0:
                pass_cnt = 5
                # await q_log.put(XmitMsg("controller","log","doing gc.collect()"))
                gc.collect()
            
        # allow co-routines to execute
        await uasyncio.sleep_ms(0)
        