# featheramin
A microcontroller-based theremin using CicuitPython and two LiDAR range detectors. 

This project uses the new, amazing, and very cool "synthio" package. 
There are so many great features in there that it's hard to know what to include and what not to. 
So as a design goal, this theremin project will try to keep it simple, 
and just support what gets us the most "theremin-y" device in the end.
Perhaps a follow-on project will explore more of what-all synthio has to offer.

## Hardware
So far, almost all components are from [Adafruit](https://www.adafruit.com). I love Adafruit!
 * Feather RP2040 microcontroller (Adafruit product ID 4884). A simpler RPi Pico could work.
 * VL53L0X Time-of-Flight distance sensor (Adafruit product ID 3317)
 * VL53L4CD Time-of-Flight distance sensor (Adafruit product ID 5396)
 * APDS-9960 proximity/gesture sensor
 * 2.2" TFT display
 * I'm still trying to figure out how to amplify this. I've used:
   * 1 watt STEMMA audio amplifier with speaker
   * 20 watt audio amp with external speaker
   * 3 watt I2S amp (the current configuration, as I2S gives better sound)
 * A TRS 1/8" headphone connector (that's stereo but so far this thing is mono)
 * a big breadboard and miscellaneous other stuff to put them together.

## Software required
 * Adafruit CircuitPython 8.2.something (currently Release Candidate 1)
 * The following Adafruit support libraries; use 'circup' to install?
   * adafruit_vl53l0x.mpy
   * adafruit_apds9960
   * adafruit_bus_device
   * adafruit_register
   * adafruit_max9744

## Dev environment
I have been using Visual Studio Code for my IDE but I don't think that matters. I have the CircuitPython extension installed, which is nice, but it is only somewhat functional as I also have my VS Code running in WSL2, which breaks some things. YMMV.

Note: The main code is in a file called "feathereminMain.py"; if you simply "include" this in your main.py, it will run. This is how I test various other modules, by incudling the code I want to run/test in main.py, rather than vaving to rename entire files to "main.py".

## Hardware config
The I2C devices are chained together in no particular order, but the 20W amplifier, when I have it connected, 
must be last in the chain because it has no StemmaQT connector and is attached via a StemmaQT pigtail.

The ILI9341 display is wired to the Feather's hardware SPI interface via 6 wires (plus ground and 3.3v).

The VL53L0X's XSHUT pin is connected to a GPIO pin so we can re-assign its address.

Currently, the PWM pin (see the code for which one) goes to the headphone jack. Alternatively it can go to the input opf whatever amplfier you are using.


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
   * Wheel: delay time
   * Wheel push: chromatic/continuous (/other - volume?)

## Things to do:
 * 3 modes? diatonic, chromatic, continuous
   * diatonic isn't that useful actually
   *   or should I say it's too complicated, but could be fun in the future
   *   ie what key? major/minor? (*which* minor?!)
 * What-all can we control?
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
     * Sine, Square, Triangle, other??
     * Can I *load* interesting waveforms?
   * Refresh/pause rate

 * Display
   * High-quality background that we can paint info onto
     * Pseudo alphanumeric LED area for text
     * Pseudo single LEDs for status (chromatic, etc?)
     * Bar graph? Meter?!

 * Controls
   * ToF
   * Gesture
   * Rotary encoder
   * Hardware volume?
   * Kill/reset switch?
 * Future?
   * Stereo
   * Line out
 * Errors
   * Flash an LED (which one?) in some error pattern.
     * Bring an LED out to box


## Notes
### Pinouts/connections for MAX98357A I2S amplifier breakout
| Pico   | Max98357A |
| ------ | --------- |
| D9     | BCLK      |
| D10    | LRC       |
| D11    | DIN       |

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


### Common Mistakes and their solutions
* Sometimes on startup, the logic for setting the I2C address of the 2nd VL53L0X doesn't work.
  * Just keep trying, it will work. (What's up with that?!)
* "RuntimeError: No pull up found on SDA or SCL; check your wiring"
  * Loose connection on StemmaQT bus (first connector in chain?)

### Display contents
| Area | Contents |
| ---- | -------- |
| T1   | Waveform |
| T2   | Sleep    | 
| T3   | LFO Mode |
| Left | Chromatic? |
| Right |        |
