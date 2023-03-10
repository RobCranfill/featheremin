# featheramin
A Feather-based theramin!

This project may or may not become a useful thing. 
I'm just having fun playing around with the Feather and its various add-ons.

## Hardware
So far, (almost) all from Adafruit!
 * Feather RP2040 microcontroller (Adafruit product ID 4884)
 * VL53L0X Time-of-Flight distance sensor (product ID 3317)
 * VL53L4CD Time-of-Flight distance sensor (product ID 5396)
 * APDS-9960 proximity/gesture sensor
 * 1 watt "Stemma" audio amplifier and speaker
 *  and/or 20 watt audio amp with external speaker
 * a breadboard or two, and a few wires to put them together!

## Software required
 * Adafruit CircuitPython 7 (version 7.3.3 used)
 * adafruit_vl53l0x.mpy
 * adafruit_apds9960 support lib (3 files)

## Dev environment
So far this code is written in CircuitPython, but I may eventually want/need to port it to C. We shall see, ha ha.

I have been using Visual Studio Code for my IDE but I don't think that matters.

Note: The main code is in a file called "main.py", to avoid the irritating warnings VSCode throws when the usual name, "code.py", is used.

## Hardware config
The I2C devices are chained together in no particular order, except the OLED display is last because it has only one STEMMA QT connector.

The STEMMA (non-QT!) amplifer's signal pin is connected to one GPIO (see the code for which one), and the VL53L0X's XSHUT pin is connected to another.


## Things to Do
 * What can I control?
   * Volume
   * Frequency
     * continuous .vs. 'chunked'
       * different scales for chunk mode?
   * Waveform
     * Sine, Square, Triangle, ???
     * Can I *load* interesting waveforms?
   * Refresh rate
 * Display
   * Some small LCD
 * Controls
   * ToF
   * Gesture
   * Rotary encoder
   * Hardware volume
   * Kill switch?
 * Future
   * Stereo
   * Headphone out

