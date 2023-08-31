""" Make noises, based on two LiDAR time-of-flight sensors.

    For CircuitPython, using the ultracool 'synthio' package.
    Build mostly (entirely?) with Adafruit components!
    See https://github.com/RobCranfill/featheremin
"""
__author__      = "Rob Cranfill"
__copyright__   = "Copyright 2023 Rob Cranfill"
__credits__     = ["Rob Cranfill", "@todbot"]
__license__     = "GPL"
__maintainer__  = "Rob Cranfill"
__email__       = "<robcranfill at gmail.com>"
__status__      = "Development"

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

# 3rd party libs (Adafruit!)
import digitalio as feather_digitalio
import synthio

# Our modules
import feathereminHardware
import featherSynth5 as fSynth
import gestureMenu


#############################################################3
# Things to do
##############
# Do we need to 'deinit' things? Which things?? Might not be a bad idea!
# Such as the GPIOs, display, sensors


# GPIO pins used
#
# The GPIO pin we use to turn the 'A' ToF sensor off,
# so we can re-program the address of the 'B' sensor.
#
L0X_A_RESET_OUT = board.D4

# The TFT display, attached via the SPI ("four wire") interface
TFT_DISPLAY_CS    = board.A2
TFT_DISPLAY_DC    = board.A0
TFT_DISPLAY_RESET = board.A1

# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_DATA = board.D11
AUDIO_OUT_I2S_WORD = board.D10


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
            ["Bogus 2",     ["A", "B", "C"], 1],
            # ["Delay",       [0, 1, 2, 3, 4, 5], 0],
            # ["Volume",      ["20", 40, 60, 80, 100], 4],
            ]

# FIXME: duplicate w/ hardware class?
def showMem():
    gc.collect()
    print(f"Free memory: {gc.mem_free()}")


# FIXME: Eventually these displayXXX methods should be moved into the display oject.

def displayLeftStatus(disp, wave, lfo):
    disp.setTextAreaL(f"{wave}\n{lfo}")

# def displayRightStatus(disp, freq):
#     disp.setTextAreaR(f"{freq:6.0f}")

def displayLFOMode(disp, mode):
    disp.setTextAreaR(mode)

def displayDroneMode(disp, freq1, freq2):
    disp.setTextAreaR(f"{freq1:4.2f} / {freq2:4.2f}")

def displayMainFreq(disp, fString):
    disp.setTextAreaR(fString)

# def displayChromaticMode(disp, chromaticFlag):
#     disp.setTextAreaL("Chromatic" if chromaticFlag else "Continuous")
#
# def displayDelay(disp, sleepMS):
#     disp.setTextArea2(f"Sleep: {sleepMS} ms")


def clamp(num, min_value, max_value):
    '''Restrict the input number to the given range.'''
    return max(min(num, max_value), min_value)

def map_and_scale(inValue, lowIn, highIn, lowOut, highOut):
    ''' Map the input number's position in the input range to the output range.'''
    frac = (inValue-lowIn)/(highIn-lowIn)
    return lowOut + frac*(highOut-lowOut)

def showFatalErrorAndHalt(errorMessage: str) -> None:
    '''An error handler for major errors, like hardware init issues.

    Perhaps flash an LED (which? - the ones on the Feather are inside the case now!)'''
    print(f"\n\nFATAL ERROR: {errorMessage}\nStopping.\n")
    while True:
        pass


# --------------------------------------------------
# ------------------- begin main -------------------
# --------------------------------------------------
def main():
    print("\nHello, Featheremin!\n")
    showMem()

    # turn off auto-reload; the auto-reload scanning seems to generate audio noise in synthio.
    # FIXME: Is this still true? Even with new versions of syntio? Even with a big buffer?
    import supervisor
    supervisor.runtime.autoreload = False  # CirPy 8 and above
    print("supervisor.runtime.autoreload = False")


    # Initialize the hardware.
    hw = feathereminHardware.FeatereminHardware(
            TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET,
            AUDIO_OUT_I2S_BIT, AUDIO_OUT_I2S_WORD, AUDIO_OUT_I2S_DATA,
            L0X_A_RESET_OUT)
    
    # could do this:
    # if not hw._intOK:
    #   ...
    tof_A, tof_B, gestureSensor, display, synth = hw.getHardwareItems()

    # What missing hardware can we tolerate?
    #####
    # Check only for the two really, really required things?
    # if tof_A is None or display is None:
    #
    if None in (tof_A, tof_B, gestureSensor, display, synth):
        print("")
        print("Some necessary hardware not found:\n")
        print(f" ToF A: {tof_A}\n ToF B: {tof_B}\n Gest: {gestureSensor}\n Disp: {display}\n Synth: {synth}")
        # print(f" Amp: {amp}\n Wheel: {wheel}\n Butt: {wheelButton}\n LED: {wheelLED}")
        return


    waveIndex = 0
    waveName = WAVEFORM_TYPES[waveIndex]
    synth.setWaveformSquare()

    lfoIndex = 0
    lfoMode = LFO_MODES[lfoIndex]
    
    displayLeftStatus(display, waveName, lfoMode)

    dSleepMilliseconds = 0

    # Play notes from a chromatic scale, as opposed to a continuous range of frequencies?
    # That is, use only integer MIDI numbers .vs. fractional?
    # False is more thereminy!
    chromatic = False
    # displayChromaticMode(display, chromatic)

    # Instructions here?
    display.setTextAreaR("Started!")

    gmenu = gestureMenu.GestureMenu(gestureSensor, display, menuData, windowSize=4)

    showMem()

    # ==== Main loop ===============================================================
    #
    while True:

        # Handle a gesture?
        #
        item, option = gmenu.getItemAndOption()
        if item is not None:
            # print(f"Gesture event: '{item}' / '{option}'")
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
                
                # print(f"drone: {f1} {f2}")
                displayDroneMode(display, f1, f2)
                synth.drone(f1, f2)
                pass

            midiNote = r1 / 5
            if midiNote > 120:
                midiNote = 120

            if chromatic:
                midiNote = int(midiNote)

            # print(f"{r1}mm -> MIDI {midiNote} -> {synthio.midi_to_hz(midiNote)}")
            # display.setTextAreaR(f"r1={r1}\nr2={r2}")

            displayMainFreq(display, f"{synthio.midi_to_hz(midiNote):4.2f} Hz")

            synth.play(midiNote)
            time.sleep(dSleepMilliseconds/100)

        else: # no proximity detected
            synth.stop()
            displayMainFreq(display, "")



# OK, let's do it! :-)
#
main()
