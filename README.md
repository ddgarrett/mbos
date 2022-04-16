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

### Wiring

TODO: a Fritzing diagram. Until then, there is a [spreadsheet showing the pins](https://docs.google.com/spreadsheets/d/16u3hJGJmb7ypCOZC1THlrIoG0V4-GSELsgmK8cBsw4Q/edit#gid=675858864).


### Software Startup

This is an experimental prototype created to explore the possibilities of running a dynamically defined system on the pico microcontroller. The startup process involves the following:

1. Run `mboss_boot.py` on the Responder. `mboss_boot.py` loads the JSON file using the builtin `ujson` module. It then starts the python module named in the JSON `main` parameter using `uasyncio.run`. On both the Responder and the Controller, the `main` module is defined by the python module `controller.py` with identical code.

2. `controller.py` will startup various services based on the contents of the JSON file `services` parameter which contains a list of  definitions for the services to be run.  In detail `controller.py` module will:

    a.  create up to two I2C objects based on I2C JSON parameters. 
    b. `controller.py` creates and runs objects for each of services included in the JSON `services` list. 
        - Each entry in the JSON `services` list defines a service including at a minimum the `name` and `module`. 
        - The `name` parameter defines a globally unique name or alias for the service. 
        - The `module` parameter is the name of the python module containing the `Service` code. 
        - The  service python module must defines a `class ModuleService(Service)` class which is a subclass of the `Service` class in `service.py`.
        - The `controller.py` loads the module, creates a new instance of `ModuleService` and then creates a `uasyncio` task using the service object `run()` method.
    c. `controller.py` then goes into a loop calling the `poll_output_queues()` method of the service defined in the JSON `ctrl_svc` parameter once during each loop iteration. In the case of the Responder, the `poll_output_queues()` method is defined in the `service_responder.py` python module.

2. Run the `mboss_boot.py` on the Controller. Just as on the Responder, this will read the `core_0_services.json` file  and startup the python module named in the JSON `main` parameter using `uasyncio.run`. As previously stated, on both the Responder and the Controller, the `main` module is defined by the python module `controller.py` with identical code with the main differences being in the contents of the JSON file defining the services.

3. `controller.py` executes the sames steps on the Controller as on the Responder. For the Controller  the`ctrl_svc` will point to a service defined by the python `service_controller.py` module instead of the `service_responder.py` module used on the Responder.


#### Poll Output Queues

To be continued...

