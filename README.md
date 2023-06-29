# featheramin
A microcontroller-based theremin using CicuitPython and two LiDAR range detectors. 

## Hardware
So far, (almost) all from Adafruit. I love Adafruit!
 * Feather RP2040 microcontroller (Adafruit product ID 4884)
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
 * adafruit_vl53l0x.mpy
 * adafruit_apds9960 support lib (3 files)

## Dev environment

I have been using Visual Studio Code for my IDE but I don't think that matters. I have the CircuitPython extension installed, which is nice, but it is only somewhat functional as I also have my VS Code running in WSL2, which breaks some things. YMMV.

Note: The main code is in a file called "feathereminMain.py"; if you simply "include" this in your main.py, it will run. This is how I test various other modules, by incudling the code I want to run/test in main.py, rather than vaving to rename entire files to "main.py".

## Hardware config
The I2C devices are chained together in no particular order, but the 20W amplifier, when I have it connected, is last in the chain because it has no Stemma connector and is attached via a Stemma pigtail.

The ILI9341 display is wired to the Feather's hardware SPI interface via 6 wires (plus ground and 3.3v).

The VL53L0X's XSHUT pin is connected to a GPIO pin so we can re-assign its address.

Currently, the PWM pin (see the code for which one) goes to the headphone jack. Alternatively it can go to the input opf whatever amplfier you are using.


## Things to Do
 * 3 modes? diatonic, chromatic, continuous
   * diatonic isn't that useful actually
   *   or should I say it's too complicated, but could be fun in the future
   *   ie what key? major/minor? (*which* minor?!)
 * NEW: Synthio
   * Main ToF: pitch
   * 2nd ToF:
     * If LFO on: LFO freq
     * If LFO off:
       * Env? which param(s)?
       * Volume?
       * These could be in the gesture cycle that selects LFO
   * Gesture:
     * Up/down: waveform (square, saw, sine)
     * L/R: LFO mode: LFO OFF / LFO vol / LFO bend
   * Wheel: delay time
   * Wheel push: chromatic/continuous/other?

 * What can I control?
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
   * <strike>Refresh rate</strike>

 * Display
   * Some small LCD

 * Controls
   * ToF
   * Gesture
   * Rotary encoder
   * Hardware volume?
   * Kill switch?
 * Future
   * Stereo
   * Line out?

