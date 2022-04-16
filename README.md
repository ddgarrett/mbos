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
    - the  `.py` files in this directory, 
    - the `/irx` and `lib` folders, 
    - the `core_0_services.json`

2. On the secondary (Responder) pic, download all of the files in `i2c_responder`.


### Wiring

TODO: a Fritzing diagram. Until then, there is a [spreadsheet showing the pins](https://docs.google.com/spreadsheets/d/16u3hJGJmb7ypCOZC1THlrIoG0V4-GSELsgmK8cBsw4Q/edit#gid=675858864). It may be slightly out of date.

