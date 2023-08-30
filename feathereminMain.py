""" Make noises, based on two LiDAR time-of-flight sensors.


"""
__author__      = "Rob Cranfill"
__copyright__   = "Copyright 2023, Rob Cranfill"
__credits__     = ["Rob Cranfill", "@todbot"]
__license__     = "GPL"
__maintainer__  = "Rob Cranfill"
__email__       = "robcranfill@gmail.com"
__status__      = "Prototype"

# Standard libs
import array
import audiocore
import board
import busio
import gc
import math
import time
import supervisor
import sys

# 3rd party libs
import digitalio as feather_digitalio

# Our modules
import feathereminHardware
import featherSynth5 as fSynth
import gestureMenu


#############################################################3
# Things to do
##############
# Do we need to 'deinit' things? Which things?? Might not be a bad idea!
# Such as the GPIOs, display, sensors


# GPIO pins used:

# for I2S audio out

# The GPIO pin we use to turn the 'A' ToF sensor off,
# so we can re-program the address of the 'B' sensor.
#
L0X_A_RESET_OUT = board.D4

TFT_DISPLAY_CS    = board.A2
TFT_DISPLAY_DC    = board.A0
TFT_DISPLAY_RESET = board.A1

AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11


# in work
USE_STEREO = True


# No 'enum' in circuitpython! :-(
MENU_WAVE = "Waveform"
WAVEFORM_TYPES = ["Sine", "Square", "Saw"]
MENU_LFO = "LFO"
LFO_MODES = ["Off", "Tremolo", "Vibrato", "Drone"]


menuData = [ # 'item', 'options', and TODO: index - or value? - of default 
            [MENU_WAVE,    WAVEFORM_TYPES, 0],
            [MENU_LFO,     LFO_MODES, 0],
            ["Chromatic",   [True, False], 0],
            ["Bogus 1",     ["A", "B", "C"], 0],
            ["Bogus 2",     ["A", "B", "C"], 1]
            # ["Delay",       [0, 1, 2, 3, 4, 5], 0],
            # ["Volume",      ["20", 40, 60, 80, 100], 4],
            ]

# FIXME: duplicate w/ hardware class?
def showMem():
    gc.collect()
    print(f"Free memory: {gc.mem_free()}")

def displayLeftStatus(disp, wave, lfo):
    disp.setTextAreaL(f"{wave}\n{lfo}")

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
    Perhaps flash an LED (which? - the ones on the Feather are inside the case now!)
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


    # Initialize the hardware.
    hw_wrapper = feathereminHardware.FeatereminHardware(
                    TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET,
                    AUDIO_OUT_I2S_BIT, AUDIO_OUT_I2S_WORD, AUDIO_OUT_I2S_DATA,
                    L0X_A_RESET_OUT)

    tof_A, tof_B, gestureSensor, display = hw_wrapper.getHardwareItems()

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
        # print(f"(Amp: {amp}\nWheel: {wheel}\nButt: {wheelButton}\nLED: {wheelLED})")
        return

    # My "synthezier" object that does the stuff that I need.
    #
    synth = fSynth.FeatherSynth(USE_STEREO,
                                i2s_bit_clock = AUDIO_OUT_I2S_BIT, 
                                i2s_word_select = AUDIO_OUT_I2S_WORD, 
                                i2s_data = AUDIO_OUT_I2S_DATA)
    synth.setVolume(0.75)


    waveIndex = 0
    waveName = WAVEFORM_TYPES[waveIndex]
    synth.setWaveformSquare()

    lfoIndex = 0
    lfoMode = LFO_MODES[lfoIndex]
    
    displayLeftStatus(display, waveName, lfoMode)

    dSleepMilliseconds = 0
    # displayDelay(display, dSleepMilliseconds)

    # iter = 1
    # wheelPositionLast = None
    # wheelButtonHeld = False

    # Play notes from a chromatic scale, as opposed to a continuous range of frequencies?
    # That is, integer MIDI numbers .vs. fractional.
    chromatic = False # more thereminy!
    # displayChromaticMode(display, chromatic)

    # Instructions here?
    display.setTextAreaR("Started!")

    # neoState = False
    # neoTime = time.monotonic_ns()

    gmenu = gestureMenu.GestureMenu(gestureSensor, display, menuData, windowSize=4)

    showMem()

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
                # print(f" -> Wave #{waveIndex}: {waveName}")

                displayLeftStatus(display, waveName, lfoMode)

                # FIXME: find a better way to do this
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
                # print(f" -> LFO #{lfoIndex}: {lfoMode}")

                displayLeftStatus(display, waveName, lfoMode)

                # FIXME: find a better way to do this
                if lfoIndex == 0:
                    synth.clearTremolo()
                    synth.clearVibrato()
                    displayLFOMode(display, "")
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


        # C'mon - make some noise!

# TODO: display frequency!

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
