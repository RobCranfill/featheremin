# featheremin
A microcontroller-based theremin using CircuitPython and two LiDAR range detectors. 

This project uses the new, amazing, and very cool "synthio" package. 
There are so many great features in there that it's hard to know what to include and what not to. 
So as a design goal, this theremin project will try to keep it simple, 
and just support what gets us the most "theremin-y" device in the end.
Perhaps a follow-on project will explore more of what-all synthio has to offer.

## Hardware
So far, almost all components are from [Adafruit](https://www.adafruit.com). I love Adafruit!
 * Feather RP2040 microcontroller (Adafruit product ID 4884). A simpler RPi Pico could work.
 * Two VL53L0X Time-of-Flight distance sensors (Adafruit product ID 3317)
 * APDS-9960 proximity/gesture sensor
 * 2.2" TFT display
 * Generic/clone [Amazon](https://a.co/d/77fnhnu) PCM5102 I2S line out breakout board (current solution)
   * Currently I am running this line out into a pair of small desktop speakers (Creative Pebble), which works really well.
   * Past audio-out experiments have included, but rejected:
     * 3 watt I2S amp
     * 1 watt STEMMA audio amplifier with speaker
     * 20 watt audio amp with external speaker
 * <strike>VL53L4CD Time-of-Flight distance sensor (Adafruit product ID 5396)</strike>
 * <strike>A rotary encoder, but I'm starting to think that's too much</strike>
 * A case, breadboard and miscellaneous other stuff to put them together.

## Software required
 * Adafruit CircuitPython 8.2.x required for new 'synthio' stuff; testing with 8.2.4.
 * The following Adafruit support libraries; use 'circup' to install? The following is the output from the circup 'freeze' command at one particular point in time; you may as well use the latest-and-greatest.
```
circup freeze
Found device at /media/rob/CIRCUITPY, running CircuitPython 8.2.2.
adafruit_vl53l0x==3.6.9
adafruit_max9744==1.2.15
adafruit_pixelbuf==2.0.2
adafruit_ili9341==1.3.10
adafruit_bus_device==5.2.6
adafruit_apds9960==3.1.8
adafruit_register==1.9.16
adafruit_seesaw==1.14.0
adafruit_bitmap_font==2.0.1
adafruit_display_text==3.0.0
```

## Dev environment
I have been using Visual Studio Code for my IDE but I don't think that matters. I have the CircuitPython extension installed, which is nice, but it is only somewhat functional as I also have my VS Code running in WSL2, which breaks some things. YMMV.

Note: The main code is in a file called "feathereminMain.py"; if you simply "include" this in your main.py, it will run. This is how I test various other modules - by incudling the code I want to run/test in main.py, rather than having to rename entire files to "main.py".

## Hardware config
The I2C devices are chained together in no particular order, but the 20W amplifier, if used,
must be last in the chain because it has no StemmaQT connector and is attached via a StemmaQT pigtail. 
(It uses I2C to set volume only, not for audio data.)

One of the VL53L0X's XSHUT pin is connected to a GPIO output pin so we can re-assign its I2C address.

The ILI9341 display is wired to the Feather's hardware SPI interface via 6 wires (plus ground and 3.3v).


## Functionality
 * Sensors:
   * Main ToF: pitch
   * 2nd ToF:
     * If LFO on: LFO freq
     * If LFO off:
       * Env? which param(s)?
       * Volume?
       * These could be in the gesture cycle that selects LFO
   * Gesture:
     * Up/down: waveform (square, saw, sine)
     * L/R: LFO mode: LFO OFF <-> LFO vol <-> LFO bend <-> Drone
   * <strike>Wheel: delay time</strike>
   * <strike>Wheel push: chromatic/continuous (/other - volume?)</strike>
   * Display
     * High-quality background that we can paint info onto - DONE, BUT USES TOO MUCH MEMORY?
       * Pseudo alphanumeric LED area for text
       * Pseudo single LEDs for status (chromatic, etc)
       * TODO: Bar graphs? Meters?!


## Things to do (some of which are done - or abandoned):
 * 3 modes? diatonic, chromatic, continuous
   * diatonic isn't actually that useful?
   *   or should I say it's too complicated, but could be fun in the future
   *   ie what key? major/minor? (*which* minor?!)
 * What-all could we control?
   * NEW: synthio params:
     * on Synthesizer:
       * waveform (overridden by Note), env (also overridden), low/high/bandpass filter
     * on Note:
       * frequency, env, filter, panning, amplitude (incl tremolo via LFO), bend (incl vibrato via LFO)
   * Volume
   * Frequency
     * continuous .vs. 'chunked'
       * different scales for chunk mode?
   * Waveform
     * Sine, Square, Saw - done
     * Triangle up/down
     * Other??
     * Can we *load* interesting waveforms?
   * Refresh/pause rate
 * Control Gadgets
   * Hardware volume?
   * Kill/reset switch? (There is one on the Feather but it's inside the box!)
 * Errors
   * Flash an LED (?) in some error pattern.
     * Bring an LED out to ? - top of box? The one on the rotary encoder? (Not quite visible)
  * Stereo - implemented, although not used much at all


## Notes

### Pinouts/connections for PCM5102 I2S line out breakout
| RP2040 | PCM5102 |
| ------ | ------- |
| D9     | BCK     |
| D10    | LCK     |
| D11    | DIN     |
| GND    | SCK     | 


### Pinouts for Adafruit 2.2" TFT and EyeSPI breakout
Pretty obvious now, but I'll document it just for fun. 
This shows two possible sets of connections: 
the first, for direct Pico-to-ILI9341 board connection; 
the second is for using the EyeSPI breakout board in-between.

| Pico   | Display | EyeSPI |
| ------ | ------- | ------ |
| MI     | -       | -      |
| MO     | MOSI    | MOSI   |
| SCK    | SCK     | SCK    |
| A2     | CS      | TCS    |
| A1     | RST     | RST    |
| A0     | DC      | DC     |
| 3v3    | Vin     | Vin    |
| GND    | Gnd     | GND    |

### I2C Addresses
We use two VL53L0X devices; by default they both have the same address, 
so we need to do some magic to make things work. See the code!

| I2 Address | Device | Notes |
| ---------- | ------ | ----- |
| 0x29       | VL53L0X #1 | Default is good |
| 0x30       | VL53L0X #2 | We must set this via software and hardware (GPIO) |
| 0x36       | Rotary Encoder | Default is OK; can change via jumper |
| 0x39       | APDS-9960 Gesture sensor | Cannot be changed |


### Pinouts/connections for MAX98357A I2S amplifier breakout (not currently used)
| RP2040 | Max98357A |
| ------ | --------- |
| D9     | BCLK      |
| D10    | LRC       |
| D11    | DIN       |


### Common Mistakes and their solutions
* Sometimes on startup, the logic for setting the I2C address of the 2nd VL53L0X doesn't work.
  * Just keep trying, it will work. (What's up with that?!)
* "RuntimeError: No pull up found on SDA or SCL; check your wiring"
  * Loose connection on StemmaQT bus (first connector in chain?)


## Demo Video
* [On YouTube](https://youtu.be/wLTpfzRJ9J0)

