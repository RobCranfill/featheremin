# featheramin
A Feather-based theramin!

This project may or may not become a useful thing. I'm just having fun playing around with the Feather and its various add-ons!

Hardware required so far, all from
Adafruit!
 * Feather RP2040 microcontroller
 * VL53L0X time-of-flight proximity sensor
 * APDS-9960 proximity/gesture sensor
 * 1 watt audio amplifier and speaker

and a breadboard and a few wires to put them together!

Software required:
 * Adafruit CircuitPython 7 (version 7.3.3 used)
 * adafruit_vl53l0x.mpy
 * adafruit_apds9960 support lib

So far this code is written in CircuitPython, but I may eventually want/need to port it to C. We shall see, ha ha.

I have been using Visual Studio Code but I don't think that matters.

Note: The main code is in a file called "main.py", to avoid the irritating warnings VCCode throws when the usual name, "code.py", is used.
