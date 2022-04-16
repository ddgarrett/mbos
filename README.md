# mbos
Microcontroller Basic Operating System

### Minimal Operating System for Microprocessors

Just a minimal OS for microcontrollers, specifically the Raspberry Pi Pico, that makes it easier 
to run multiple programs and sensors on a single microcontroller. Running a number of apps on a single
microcontroller has become a reality now
that there are very powerful microcontrollers, such as the Raspberry Pi Pico which comes with a 133 MHz CPU, 264 kB RAM and 2 MB of flash drive.
This is more powerful than the original IBM PC, yet costs just $4 (well... in reality, good luck
trying to get one below $8) versus the original IBM PC which cost $1,565 (equivalent to $4,455 in 2020 dollars).

The Raspberry Pi Pico probably deserves an OS much better than this, but hey, it's a start :-)

### Main Goals

1. Allow multiple "services" to be run on a single microprocess, as defined in a .json file

2. Allow "plug and play" additions of other microprocessors, Pico and non-Pico


### To Run

1. On the primary (Controller) pico, download:
    - the  micropython `.py` files in this directory, 
    - the `/irx` and `lib` folders, 
    - the `core_0_services.json` file which defines the startup configuration.

2. On the secondary (Responder) pico, download all of the files in the `i2c_responder` folder.

3. Ignore the files in the `i2c_responder_v004.ino` folder. They were originally used for some testing with the Arduino Uno, but are out of date.

4. Startup the Responder pico first, running the `mbos_boot.py` file on the Responder microcontroller. 

5. Startup the Controller pico by also running the `mbos_boot.py` file that microcontroller.

At this point you should see a display on the LCD. Use the `⏶` and `⏷` keys to scroll up and down through the list of services. When the IR Remote key is accepted you'll see an hourglass symbol, `⌛`, in the bottom right of the LCD.

### To Stop

1. Controller must be shut down first or else it will hang

2. Shut down Responders after shutting down the Controller

3. If the Responder is shut down first, run `i2c_test.py` on the Responder. This will run an I2C scan which seems to cause an IO error on the Controller if its I2C connection is hung on a send or receive


### Wiring

TODO: a Fritzing diagram. Until then, there is a [spreadsheet showing the pins](https://docs.google.com/spreadsheets/d/16u3hJGJmb7ypCOZC1THlrIoG0V4-GSELsgmK8cBsw4Q/edit#gid=675858864).


### Software Startup

This is an experimental prototype created to explore the possibilities of running a dynamically defined system on the pico microcontroller. The startup process involves the following:

1. Run `mboss_boot.py` on the Responder. `mboss_boot.py` loads the JSON file using the builtin `ujson` module. It then starts the python module named in the JSON `main` parameter using `uasyncio.run`. On both the Responder and the Controller, the `main` module is defined by the python module `controller.py` with identical code.

2. `controller.py` will startup various services based on the contents of the JSON file `services` parameter which contains a list of  definitions for the services to be run.  In detail `controller.py` module will:

    a.  create up to two I2C objects based on I2C JSON parameters. 

    b. `controller.py` creates and runs objects for each of services included in the JSON `services` list. 

    c.  Each entry in the JSON `services` list defines a service including at a minimum the `name` and `module`. 

    d. The `name` parameter defines a globally unique name or alias for the service. 

    e. The `module` parameter is the name of the python module containing the `Service` code. 

    f.  The  service python module must defines a `class ModuleService(Service)` class which is a subclass of the `Service` class in `service.py`.

    g. The `controller.py` loads the module, creates a new instance of `ModuleService` and then creates a `uasyncio` task using the service object `run()` method.

    h. `controller.py` then goes into a loop calling the `poll_output_queues()` method of the service defined in the JSON `ctrl_svc` parameter once during each loop iteration. In the case of the Responder, the `poll_output_queues()` method is defined in the `service_responder.py` python module.

2. Run the `mboss_boot.py` on the Controller. Just as on the Responder, this will read the `core_0_services.json` file  and startup the python module named in the JSON `main` parameter using `uasyncio.run`. As previously stated, on both the Responder and the Controller, the `main` module is defined by the python module `controller.py` with identical code with the main differences being in the contents of the JSON file defining the services.

3. `controller.py` executes the sames steps on the Controller as on the Responder. For the Controller  the`ctrl_svc` will point to a service defined by the python `service_controller.py` module instead of the `service_responder.py` module used on the Responder.

##### Example Controller Services JSON Parm

```json
"services": [
    {"name":"controller",    "module":"service_controller",   "q_out_size":10,
        "startup_focus":"menu",  "menu":"menu" },
         
    {"name":"menu",          "module":"service_menu",     "initial_app":"temp_humid",  
        "menu":[ "temp_humid", "gyro", "mem_use", "clock"]
        },

    {"name":"lcd",           "module":"service_lcd_v02",  "custom_char":"°⏴⏵⏶⏷⌛" },
        
    {"name":"temp_humid",    "module":"service_dht11_v02" },
        
    {"name":"i2c_svc",       "module":"service_i2c_controller", "q_in_size":50, "q_out_size":50,
     "ignore_addr":[104], "i2c_parm":"i2c_1" },
    
    
    {"name":"gyro",          "module":"svc_gyro_v01", "adj_x":-4, "i2c_parm":"i2c_1"},
        
    {"name":"log",           "module":"service_print",  "q_in_size":100,  "print_log":1,
      "todo": "make a log to disk version, or have that as an option?" },
        
    {"name":"ir_remote",     "module":"service_ir",     "key_map":"ir_mapping_koobook.json" },
    {"name":"mem_use",       "module":"service_mem_use"   },
    {"name":"clock",         "module":"service_clock"   }
    
 ],

```

#### Interservice Communication

- Services communicate via `uasyncio` based FIFO queues as defined in the `lib\queue.py` module. 

- Each service has two queues: input and output.
- Each record in the queue is a class or subclass of type `XmitMsg` as defined in the python module `xmit_message.py`.
- Records specify:
    - From: name of service sending the message
    - To: name of service receving the message
    - Message: the message being sent. Usually text, list, dictionary or list of dictionaries (key value pairs)
- The `poll_output_queues()` method called by the `controller` checks the output queues passing each output record to the input queue for the specified service.
- On Responders, if the receiving service is not a named service on the Responder, the message is passed to the Controller.
- On the Controller, if it does not recognize the receiving service, the message is discarded.

#### Inter-microcontroller Startup

- When the system starts up, `controller.py` will create up to two I2C objects based on parameters in the JSON file.
    - placed in a `defaults` dictionary available to all services under the names `i2c` and `i2c_1`
    - if the parameters for an I2C bus specifies a value for `i2c_responder_addr`, the `controller.py` assumes the I2C bus is for an I2C Responder and creates a new instance of `I2CResponder` as defined in `i2c_responder.py`. 
    - Otherwise, `controller.py` will create a new I2C instance from the standard `machine.I2C` class

- The Controller `services` JSON parameters defines a service named `i2c_svc` started from the python class `service_i2c_controller.ModuleService`. The `run()` method for the `i2c_svc` service will
    1. scan the I2C bus specified by the `i2c_parm` service parameter, which should be `i2c` or `i2c_1`, to obtain the list of Responders. 
    2. The service parameter `ignore_addr` must contain a list of I2C addresses on that bus which are **not** MBOS Responders. If a non-Responder I2C bus member is not specified this will hang the Controller.
    3. The `i2c_svc` will then transmit a message to each Responder, which will be directed at the Responder `pnp_svc`, with the message `ext_svc`.

- The loading of external services then continues as follows:
    1. The Responder `pnp_svc`, if any, will then respond to the `ext_svc` message with a list of external services that should be added to the list of services on the Controller. 
    5. The response message is sent to the xmit `from` service, which will be the service named `controller` (`service_controller.py` based service) which runs only on the Controller
    6. The Controller `controller` service then adds the services to the list of Controller services after creating a new instance of the service and starting its `run()` method. This means that the source for the python module must exist on the Controller. **TODO**: limit which python modules can be started this way? Currently only `svc_i2c_stub.py` and `svc_test_i2c.py` modules are used to start remote services on the Controller. The `svc_i2c_stub.py` simply forwards a message to the specified Responder based on the Responder address.
    7. After starting the remote services for the Responder `pnp_svc`, the `controller` service on the Controller sends a second xmit to the `pnp_svc` with the message `ext_menu`. This tells the `pnp_svc` to respond to the Controller `menu` service with a list of service names to be added to the Controller menu.
    8. The Responder `pnp_svc` service optionally responds with the value of the services `ext_menu` list, which is sent to the `menu` service on the Controller.
    9. The Controller `menu` service then appends these to the Controller menu, the list of services which are scrolled through via the the `⏶` and `⏷` keys.

##### Example Responder JSON Services Parm with Plug and Play JSON Parms

```json
"services": [
    {"name":"0x41_log",      "module":"service_print",      "q_in_size":1000,  "print_log":1 },
        
    {"name":"0x41_mem_use",  "module":"service_mem_use" },
    
    {"name":"i2c_svc",       "module":"svc_i2c_responder",  "q_in_size":1000,  "print_log":1 },
    
    {"name":"0x41_test_i2c", "module":"svc_test_i2c",       "send_to":"log" },
 
    {"name":"0x41_ctrl",     "module":"service_responder",  "q_out_size":50, "i2c_svc":"i2c_svc" },
    
    {"name":"pnp_svc",       "module":"svc_pnp",            "q_out_size":50, "i2c_svc":"i2c_svc",
     "ext_svc":[
            {"name":"0x41_log",      "module":"svc_i2c_stub",   "forward_i2c_addr":"0x41" },
            {"name":"0x41_mem_use",  "module":"svc_i2c_stub",   "forward_i2c_addr":"0x41" },
            {"name":"0x41_test_i2c", "module":"svc_i2c_stub",   "forward_i2c_addr":"0x41" },
            {"name":"test_i2c_0x41", "module":"svc_test_i2c",   "send_to":"0x41_log" }

        ],
        
      "ext_menu":["0x41_mem_use","test_i2c_0x41", "0x41_test_i2c" ]
      
    }
  ],
```

#### Inter-microcontroller Messages

How messages are wrapped and unwrapped

Details of communicaton of I2C messages with checksums and blocks, etc.? See next section.

#### Inter-microcontroller I2C Protocol

Details of how messages are sent via I2C sending first the length of the message, then 16 byte blocks for the message, each block followed by a checksum and acknowledgement.

Also how Controller does control the message exchange. Responders should be ready at any time to send any messages or a zero length message if no messages are available.

Controller pauses roughly 100ms between iterations of sending any messages and polling all Responders for any messages. (Should this be longer?)

Controller also does an `await uasyncio.sleep_ms(0)` call between sending messages to Responders, polling Responders and receiving a message from a Responder.

During startup, the `controller.py` module will start a responder task.

```python
    resp_addr = get_parm(parms,"i2c_responder_addr",None)

    if resp_addr != None:
        # we're an I2C Responder
        i2cr = I2CResponder(bus, sda_gpio=sda, scl_gpio=scl,
                            responder_address=resp_addr)
        
        uasyncio.create_task(i2cr.poll_snd_rcv())
```

The `I2CRepsonder.create_task()` method then continually checks for the Controller read and write requests, performing a `await uasyncio.sleep_ms(0)` only if there aren't any Controller requests. In other words, it should respond almost immediately when the Controller tries to send or receive data. This seemed to reduce the 
instance of transmit errors.