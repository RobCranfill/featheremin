"""Make noises, based on various sensors including time-of-flight.
    robcranfill@gmail.com
"""
import array
import audiocore
import board
import busio
import digitalio as feather_digitalio
import gc
import math
import time
import supervisor
import sys


#############################################################3
# Things to do
##############
# Do we need to 'deinit' things? Which things?? Might not be a bad idea!
# Such as the GPIOs, display, sensors


# Adafruit hardware libraries - www.adafruit.com
import adafruit_vl53l0x
import adafruit_max9744
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel

# Other Featheremin modules

import featherSynth5 as fSynth
import gestureMenu


# in work
USE_STEREO = True


# No 'enum' in circuitpython! :-(
MENU_WAVE = "Waveform"
WAVEFORM_TYPES = ["Sine", "Square", "Saw"]
MENU_LFO = "LFO"
LFO_MODES = ["Off", "Tremolo", "Vibrato", "Drone"]

# GPIO pins used:
# The GPIO pin we use to turn the 'primary' ("A") ToF sensor off,
# so we can re-program the address of the secondary one.
L0X_A_RESET_OUT = board.D4

# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

# TFT display
USE_SIMPLE_DISPLAY = True
if USE_SIMPLE_DISPLAY:
    import feathereminDisplay3 as fDisplay
else:
    import feathereminDisplay2 as fDisplay

TFT_DISPLAY_CS    = board.A2
TFT_DISPLAY_DC    = board.A0
TFT_DISPLAY_RESET = board.A1

# The L0X defaults to I2C 0x29; we have two, one of which we will re-assign to this address.
L0X_B_ALTERNATE_I2C_ADDR = 0x30

ROTARY_ENCODER_I2C_ADDR = 0x36
SEE_SAW_BUTTON_PIN_WTF = 24  # FIXME: wtf is this magic number?

INITIAL_20W_AMP_VOLUME = 10 # 25 is max for 20W amp and 3W 4 ohm speaker with 12v to amp.

menuData = [ # 'item', 'options', and TODO: index - or value? - of default 
            [MENU_WAVE,    WAVEFORM_TYPES, 0],
            [MENU_LFO,     LFO_MODES, 0],
            ["Chromatic",   [True, False], 0],
            ["Bogus 1",     ["A", "B", "C"], 0],
            ["Bogus 2",     ["A", "B", "C"], 1]
            # ["Delay",       [0, 1, 2, 3, 4, 5], 0],
            # ["Volume",      ["20", 40, 60, 80, 100], 4],
            ]

def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()


def init_hardware() -> tuple[adafruit_vl53l0x.VL53L0X,   # 'A' ToF sensor
                            adafruit_vl53l0x.VL53L0X,    # 'B' ToF sensor
                            APDS9960,                    # gesture sensor
                            fDisplay.FeathereminDisplay, # our display object
                            adafruit_max9744.MAX9744,    # big amplifier, or None
                            rotaryio.IncrementalEncode,  # rotary encoder
                            digitalio.DigitalIO,         # pushbutton in rotary encoder
                            neopixel.NeoPixel            # neopixel in rotary encoder
                            ]:
    
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensors, gesture sensor, display, and amp (if attached).

    Mostly none of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various hardware items initialized.
    """

    # supervisor.reload()

    # Easist way to init I2C on a Feather:
    try:
        i2c = board.STEMMA_I2C()
    except:
        print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")
        return tuple()

    # For fun
    showI2Cbus()


    # FIXME: how do we do overloaded contsructors???
    if USE_SIMPLE_DISPLAY:
    # ----------------- Our display object - do this early so we can show errors?
        display = fDisplay.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET, 4)
    else:
        display = fDisplay.FeathereminDisplay(180, False, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)

    print("Display init OK")


    # ----------------- 'Primary' VL53L0X time-of-flight sensor
    # 'Primary' ToF - this has its XSHUT pin wired to GPIO {L0X_A_RESET_OUT}.
    # We will finish setting this sensor up 
    # *after* we turn it off and init the 'secondary' ToF sensor.
    
    # Turn off this ToF sensor - take XSHUT pin low.
    #
    print("Turning off 'primary' VL53L0X...")
    L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
    L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
    L0X_A_reset.value = False

    # Prmary VL53L0X sensor is now turned off
    showI2Cbus()


    # ----------------- 'Secondary' VL53L0X time-of-flight sensor
    # 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
    # First, see if it's there already with the non-default address (left over from a previous run).
    # If so, we don't need to re-assign it.
    try:
        L0X_B = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
        print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
    except:
        print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
        try:
            # Try at the default address
            L0X_B = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
            print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
            L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
            print("VL53L0X set_address OK")

            # Set params for the sensor?
            # # The default timing budget is 33ms, a good compromise of speed and accuracy.
            # # For example a higher speed but less accurate timing budget of 20ms:
            # L0X_B.measurement_timing_budget = 20000
            # # Or a slower but more accurate timing budget of 200ms:
            # L0X_B.measurement_timing_budget = 200000

            print("Secondary VL53L0X init OK")
        except Exception as e:
            print(f"**** Caught exception: {e}")
            print("**** No secondary VL53L0X?")
            L0X_B = None


    # ----------------- VL53L0X time-of-flight sensor, part 2
    # Turn L0X back on and instantiate its object
    print("Turning 'primary' VL53L0X back on...")
    L0X_A_reset.value = True
    L0X_A = None
    try:
        L0X_A = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
        # Set params for the sensor?

        print("'Primary' VL53L0X init OK")
    except:
        print("**** No primary VL53L0X? Continuing....")

    # Show bus again?
    showI2Cbus()


    # ----------------- APDS9960 gesture/proximity/color sensor
    apds = None
    try:
        apds = APDS9960(i2c)
        apds.enable_proximity = True
        apds.enable_gesture = True
        apds.rotation = 90
        print("APDS9960 init OK")
    except:
        print("**** No APDS9960? Continuing....")


    # ------------------ MAX9744 amp, if any
    # TODO: merge this into the Synth object? Or at least hand it to that object to use?
    amp = None
    # try:
    #     amp = adafruit_max9744.MAX9744(i2c)
    #     amp.volume = INITIAL_20W_AMP_VOLUME
    #     print("MAX9744 amp init OK")
    # except Exception as e:
    #     print(f"No MAX9744 amplifier found: '{e}' - OK?")
    #     amp = None

    # ------------------ Rotary encoder
    encoder, wheel_button, pixel = None, None, None
    # try:
    #     ss = seesaw.Seesaw(i2c, addr=ROTARY_ENCODER_I2C_ADDR)
    #     seesaw_v = (ss.get_version() >> 16) & 0xFFFF
    #     # print(f"Found product {seesaw_v}")
    #     if seesaw_v != 4991:
    #         print("Wrong rotary encoder firmware version? Continuing...")
    #         # what are we supposed to do about this??
    #     encoder = rotaryio.IncrementalEncoder(ss)
    #
    #     # the "button" that is got by pushing down on the encoder wheel
    #     ss.pin_mode(SEE_SAW_BUTTON_PIN_WTF, ss.INPUT_PULLUP)
    #     wheel_button = digitalio.DigitalIO(ss, 24)
    #
    #     # TODO: tried to do something with the Neopixel but haven't figured anything out yet. :-/
    #     pixel = neopixel.NeoPixel(ss, 6, 1)
    #   
    #     pixel.fill(0x000100) # very light green - for go!
    #     # pixel.brightness = 0.1
    #
    #     print("Rotary encoder init OK")
    #
    # except:
    #     print(f"\n**** No rotary encoder at I2C {hex(ROTARY_ENCODER_I2C_ADDR)}? OK\n")


    showMem()
    print("")
    print("init_hardware OK!")
    print("")

    return L0X_A, L0X_B, apds, display, amp, encoder, wheel_button, pixel

    # end init_hardware()


def showMem():
    gc.collect()
    print(f"Free memory: {gc.mem_free()}")

def displayWaveformName(disp, name):
    disp.setTextAreaL(name)

def displayLFOMode(disp, mode):
    disp.setTextAreaR(mode)

# def displayChromaticMode(disp, chromaticFlag):
#     disp.setTextAreaL("Chromatic" if chromaticFlag else "Continuous")
#
# def displayDelay(disp, sleepMS):
#     disp.setTextArea2(f"Sleep: {sleepMS} ms")


'''
 Restrict the input number to the given range.
'''
def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

'''
    Map the input number's position in the input range to the output range.
'''
def map_and_scale(inValue, lowIn, highIn, lowOut, highOut):
    frac = (inValue-lowIn)/(highIn-lowIn)
    return lowOut + frac*(highOut-lowOut)

'''
    An error handler for major errors, like hardware init issues.
    Perhaps flash an LED (which one? - the ones on the Feather are inside the case now!)
'''
def showFatalErrorAndHalt(errorMessage: str):
    print(f"\n\nFATAL ERROR: {errorMessage}\nStopping.\n")
    while True:
        pass


# --------------------------------------------------
# ------------------- begin main -------------------
# --------------------------------------------------
def main():
    print("\nHello, Featheremin!\n")
    showMem()

    # turn off auto-reload?
    import supervisor
    supervisor.runtime.autoreload = False  # CirPy 8 and above
    print("supervisor.runtime.autoreload = False")

    # Initialize the hardware, dying if something critical is missing.
    # Just plain None back is super bad.
    #
    hw_result = init_hardware()
    if hw_result is tuple(): # FIXME: doesn't work right
        showFatalErrorAndHalt("init_hardware failed!")

    tof_A, tof_B, gestureSensor, display, amp, wheel, wheelButton, wheelLED = hw_result
    
    # What missing hardware can we tolerate?
    #####
    # Check only for the two really, really required things?
    # if tof_A is None or display is None:
    #
    # Check for anything missing?
    # if None in (tof_A, tof_B, gestureSensor, display, amp, wheel, wheelButton, wheelLED):
    #
    # No MAX9744 amp is always OK
    # if None in (tof_A, tof_B, gestureSensor, display, wheel, wheelButton, wheelLED):

    if None in (tof_A, tof_B, gestureSensor, display):

        print("")
        print("Necessary hardware not found.\n")
        print(f"ToF A: {tof_A}\nToF B: {tof_B}\nGest: {gestureSensor}\nDisp: {display}")
        print(f"(Amp: {amp}\nWheel: {wheel}\nButt: {wheelButton}\nLED: {wheelLED})")
        return

    # My "synthezier" object that does the stuff that I need.
    #
    # synth = featherSynth5.FeatherSynth(AUDIO_OUT_PIN)
    synth = fSynth.FeatherSynth(USE_STEREO,
                                i2s_bit_clock=AUDIO_OUT_I2S_BIT, 
                                i2s_word_select=AUDIO_OUT_I2S_WORD, 
                                i2s_data=AUDIO_OUT_I2S_DATA)
    synth.setVolume(0.75)

    # FIXME:
    waveIndex = 0
    waveName = WAVEFORM_TYPES[waveIndex]
    displayWaveformName(display, waveName)
    synth.setWaveformSquare()

    lfoIndex = 0
    lfoMode = LFO_MODES[lfoIndex]
    # displayLFOMode(display, lfoMode)

    dSleepMilliseconds = 0
    # displayDelay(display, dSleepMilliseconds)

    # iter = 1
    wheelPositionLast = None

    # Play notes from a chromatic scale, as opposed to a continuous range of frequencies?
    # That is, integer MIDI numbers .vs. fractional.
    chromatic = True
    # displayChromaticMode(display, chromatic)

    # Instructions here?
    display.setTextAreaR("Started!")

    wheelButtonHeld = False

    neoState = False
    neoTime = time.monotonic_ns()

    gmenu = gestureMenu.GestureMenu(gestureSensor, display, menuData, windowSize=4)

    showMem()

    #
    # ==== Main loop ===============================================================
    #
    while True:

        # Handle a gesture?
        #
        item, option = gmenu.getItemAndOption()
        if item is not None:
            print(f"Gesture event: '{item}' / '{option}'")
            if item == MENU_WAVE:
                waveName = option
                waveIndex = WAVEFORM_TYPES.index(waveName)
                print(f" -> Wave #{waveIndex}: {waveName}")
                displayWaveformName(display, waveName)
                # FIXME: a better way to do this?
                if waveIndex == 0:
                    synth.setWaveformSquare()
                elif waveIndex == 1:
                    synth.setWaveformSine()
                elif waveIndex == 2:
                    synth.setWaveformSaw()

            elif item == MENU_LFO:
                lfoMode = option
                lfoIndex = LFO_MODES.index(lfoMode)
                lfoMode = LFO_MODES[lfoIndex]
                print(f" -> LFO #{lfoIndex}: {lfoMode}")

                # displayLFOMode(display, lfoMode)

                if lfoIndex == 0:
                    synth.clearTremolo()
                    synth.clearVibrato()
                elif lfoIndex == 1: # tremolo
                    synth.setTremolo(20)
                    synth.clearVibrato()
                elif lfoIndex == 2: # vibrato
                    synth.setVibrato(20)
                    synth.clearTremolo()
                elif lfoIndex == 3: # dual/drone
                    synth.clearVibrato()
                    synth.clearTremolo()
                    synth.startDrone(1000, 1100)


        # Make some noise!

        # Get the two ranges, as available. 
        #
        # r1 is the main ToF detector, used for main frequency.
        # r2 is the secondary ToF, used for LFO freq, and maybe other things.
        #
        r1 = tof_A.range
        # print(f"Range A: {r1}, range B: {r2}")

        # Only read ToF2 if ToF1 is close - TODO: how close?
        # TODO: if not in a mode that uses this ToF2, don't read it?
        if r1 > 0 and r1 < 1000:

            r2 = tof_B.range
            if r2 > 50 and r2 < 500:
                # TODO: REWORK THIS
                # - We do get readings farther out, to like XXXX at 2 feet, but will use only the closer range?
                # TODO: Use values XXXX for now; tailor for trem/vib?
                # sometimes there seem to be false signals of 0, so toss them out.
                r2a = max(5, r2)
                # print(f"r2: {r2} -> r2a = {r2a}")

                # TODO: only set if r2 has *changed*? especially if we force the value to be an int.
                
                # if mode was changed, the "other" mode has already been cleared, so we are good to go.
                if lfoIndex == 1: # tremolo
                     # map to 8-16?
                    trem = map_and_scale(r2, 50, 500, 8, 16)
                    # print(f"r2 {r2} -> trem {trem}")
                    displayLFOMode(display, f"T @ {trem:.1f}")
                    synth.setTremolo(trem)

                elif lfoIndex == 2:
                    # map to 4-10?
                    vib = map_and_scale(r2, 50, 500, 4, 10)
                    synth.setVibrato(r2a) 
                    # print(f"r2 {r2} -> vib ?")
                    displayLFOMode(display, f"V @ {vib:.1f}")

            # drone mode
            if lfoIndex == 3:
                f1 = clamp(r1*100, 1000, 20000)
                
                # f2 = clamp(r2*100, 1000, 20000)
                f2 = f1 - r2
                
                print(f"drone: {f1} {f2}")
                synth.drone(f1, f2)
                pass

            midiNote = r1 / 4
            if midiNote > 120:
                midiNote = 120

            if chromatic:
                midiNote = int(midiNote)

            # print(f"{r1} -> {midiNote}")
            # display.setTextAreaR(f"r1={r1}\nr2={r2}")

            synth.play(midiNote)
            time.sleep(dSleepMilliseconds/100)

        else: # no proximity detected
            synth.stop()

        # iter += 1

# OK, let's do it! :-)
#
main()
