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

#### Inter-microcontroller Messages

- When the system starts up, `controller.py` will create up to two I2C objects based on parameters in the JSON file.
    - placed in a `defaults` dictionary available to all services under the names `i2c` and `i2c_1`
    - if the parameters for an I2C bus specifies a value for `i2c_responder_addr`, the `controller.py` assumes the I2C bus is for an I2C Responder and creates a new instance of `I2CResponder` as defined in `i2c_responder.py`. 
    - Otherwise, `controller.py` will create a new I2C instance from the standard `machine.I2C` class

- The Controller `services` JSON parameters defines a service named `i2c_svc` started from the python class `service_i2c_controller.ModuleService`. The `run()` method for the `i2c_svc` service will
    1. scan the I2C bus specified by the `i2c_parm` service parameter, which should be `i2c` or `i2c_1`, to obtain the list of Responders. 
    2. The service parameter `ignore_addr` must contain a list of I2C addresses on that bus which are **not** MBOS Responders. If a non-Responder I2C bus member is not specified this will hang the Controller.
    3. The `i2c_svc` will then transmit a message to each Responder, which will be directed at the Responder `pnp_svc`, with the message `ext_svc`.

- The loading of external services then continues as follows:
    1. The Responder `pnp_svc` will then respond to the `ext_svc` message with a list of external services that should be added to the list of services on the Controller. 
    5. The response message is sent to the xmit `from` service, which will be the Controller service named `controller` (`service_controller.py` based service)
    6. The Controller `controller` service then adds the services to the list of Controller services after creating a new instance of the service and starting its `run()` method. This means that the source for the python module must exist on the Controller. **TODO**: limit which python modules can be started this way? Currently only `svc_i2c_stub.py` and `svc_test_i2c.py` modules are used to start remote services on the Controller. The `svc_i2c_stub.py` simply forwards a message to the specified Responder based on the Responder address.
    7. After starting the remote services for the Responder `pnp_svc`, the `controller` service on the Controller sends a second xmit to the `pnp_svc` with the message `ext_menu`. This tells the `pnp_svc` to respond to the Controller `menu` service with a list of service names to be added to the Controller menu.
    8. The Responder `pnp_svc` service responds with the value of the services `ext_menu` list, which is sent to the `menu` service on the Controller.
    9. The Controller `menu` service then appends these to the Controller menu, the list of services which are scrolled through via the the `⏶` and `⏷` keys.
