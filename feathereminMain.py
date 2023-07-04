"""Make noises, based on various sensors including time-of-flight.
    robcranfill@gmail.com
"""
import array
import audiocore
# import audiopwmio
import board
import busio
import digitalio as feather_digitalio
import math
import time
import supervisor
import sys

# Adafruit hardware libraries - www.adafruit.com
import feathereminDisplay9341
import adafruit_vl53l0x
# import adafruit_vl53l4cd
import adafruit_max9744
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel

import featherSynth5

# No 'enum' in circuitpython! :-(
# from enum import Enum
# class Waveform(Enum):
#     SQUARE = 1
#     SINE = 2
#     SAW = 3
WAVEFORM_TYPES = ["Square", "Sine", "Saw"]
LFO_MODES = ["LFO Off", "Tremolo", "Vibrato", "Drone"]
lfo_tremolo_freq = 15
lfo_vibrato_freq = 4

# GPIO pins used:
# The GPIO pin we use to turn the 'primary' ("A") ToF sensor off,
# so we can re-program the address of the secondary one.
L0X_A_RESET_OUT = board.D4

# for PWM audio output
# AUDIO_OUT_PIN = board.D5    

# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

# Display
TFT_DISPLAY_CS    = board.A2
TFT_DISPLAY_DC    = board.A0
TFT_DISPLAY_RESET = board.A1

# The L0X defaults to I2C 0x29; we have two, one of which we will re-assign to this address.
L0X_B_ALTERNATE_I2C_ADDR = 0x31

ROTARY_ENCODER_I2C_ADDR = 0x36
SEE_SAW_BUTTON_PIN_WTF = 24  # FIXME: wtf is this magic number?

INITIAL_AMP_VOLUME = 10 # 25 is max for 20W amp and 3W 4 ohm speaker with 12v to amp.


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()


def init_hardware() -> list(adafruit_vl53l0x.VL53L0X,    # 'A' ToF sensor
                            adafruit_vl53l0x.VL53L0X,    # 'B' ToF sensor
                            APDS9960,                    # gesture sensor
                            feathereminDisplay9341.FeathereminDisplay9341, # our display object
                            adafruit_max9744.MAX9744,    # big amplifier, or None
                            rotaryio.IncrementalEncoder, # rotary encoder
                            digitalio.DigitalIO,         # pushbutton in rotary encoder
                            neopixel.NeoPixel            # neopixel in rotary encoder
                            ):
    
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensors, gesture sensor, display, and amp (if attached).

    Mostly none of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various hardware items initialized.
    """

    # supervisor.reload()

    # Easist way to init I2C on a Feather:
    i2c = board.STEMMA_I2C()

    # For fun
    showI2Cbus()

    # ----------------- VL53L0X time-of-flight sensor 
    # We will finish setting this sensor up 
    # *after* we turn it off and init the 'secondary' ToF sensor.
    
    # Turn off the ToF sensor - take XSHUT pin low
    print("Turning off primary VL53L0X...")
    L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
    L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
    L0X_A_reset.value = False
    # VL53L0X sensor is now turned off
    showI2Cbus()


    # ----------------- VL53L4CD time-of-flight sensor
    # 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
    # First, see if it's there with the new address (left over from a previous run).
    # If so, we don't need to re-assign it.
    try:
        L0X_B = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
        print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
    except:
        print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
        try:
            L0X_B = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
            print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
            L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
            print("VL53L0X set_address OK")

            # # set non-default values?
            L0X_B.inter_measurement = 0
            L0X_B.timing_budget = 100
            L0X_B.start_ranging()

            # print("--------------------")
            # print("VL53L4CD:")
            # model_id, module_type = L4CD.model_info
            # print(f"    Model ID: 0x{model_id:0X}")
            # print(f"    Module Type: 0x{module_type:0X}")
            # print(f"    Timing Budget: {L4CD.timing_budget}")
            # print(f"    Inter-Measurement: {L4CD.inter_measurement}")
            # print("--------------------")
            print("secondary VL53L0X init OK")
        except:
            print("**** No secondary VL53L0X?")
            L0X_B = None


    # ----------------- VL53L0X time-of-flight sensor, part 2
    # Turn L0X back on and instantiate its object
    print("Turning VL53L0X back on...")
    L0X_A_reset.value = True
    L0X_A = None
    try:
        L0X_A = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
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

    # ----------------- Our display object
    display = feathereminDisplay9341.FeathereminDisplay9341(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)
    print("Display init OK")

    # ------------------ MAX9744 amp, if any
    amp = None
    try:
        amp = adafruit_max9744.MAX9744(i2c)
        amp.volume = INITIAL_AMP_VOLUME
        print("MAX9744 amp init OK")
    except:
        print("**** No MAX9744 amplifier found; continuing....")

    # ------------------ Rotary encoder
    encoder, wheel_button, pixel = None, None, None
    try:
        ss = seesaw.Seesaw(i2c, addr=ROTARY_ENCODER_I2C_ADDR)
        seesaw_v = (ss.get_version() >> 16) & 0xFFFF
        # print(f"Found product {seesaw_v}")
        if seesaw_v != 4991:
            print("**** Wrong Rotary encoder firmware loaded?  Expected 4991")
            # what are we supposed to do about this??
        encoder = rotaryio.IncrementalEncoder(ss)

        # the "button" that is got by pushing down on the encoder wheel
        ss.pin_mode(SEE_SAW_BUTTON_PIN_WTF, ss.INPUT_PULLUP)
        wheel_button = digitalio.DigitalIO(ss, 24)

        # TODO: tried to do something with the Neopixel but haven't figured anything out yet. :-/
        pixel = neopixel.NeoPixel(ss, 6, 1)
        # pixel.brightness = 0.1
        pixel.fill(0x004000) # green for go!
        print("Rotary encoder init OK")
    
    except:
        print(f"\n**** No rotary encoder at I2C {hex(ROTARY_ENCODER_I2C_ADDR)}? Can't continue!\n")
        # return


    print("\ninit_hardware OK!\n")
    
    return L0X_A, L0X_B, apds, display, amp, encoder, wheel_button, pixel


def displayChromaticMode(disp, chromaticFlag):
    disp.setTextAreaL("Chromatic" if chromaticFlag else "Continuous")

def displayDelay(disp, sleepMS):
    disp.setTextArea2(f"Sleep: {sleepMS} ms")

def displayWaveformName(disp, name):
    disp.setTextArea1(f"Waveform: {name}")

def displayLFOMode(disp, mode):
    disp.setTextArea3(mode)

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

'''
    Map the input number's position in the input range to the output range.
'''
def map_and_scale(inValue, lowIn, highIn, lowOut, highOut):
    frac = (inValue-lowIn)/(highIn-lowIn)
    return lowOut + frac * (highOut-lowOut)

# --------------------------------------------------
# ------------------- begin main -------------------
def main():
    print("\nHello, Featheremin!\n")

    # turn off auto-reload?
    import supervisor
    supervisor.runtime.autoreload = False  # CirPy 8 and above
    print("supervisor.runtime.autoreload = False")

    # Initialize the hardware, dying if something critical is missing.
    #
    tof_A, tof_B, gestureSensor, display, amp, wheel, wheelButton, wheelLED = init_hardware()

    if tof_A is None or display is None:
        print("\n AUGHHHHHHH !!!!!\n\n")
        print("Necessary hardware not found.\n")
        return

    # My "synthezier" object that does the stuff that I need.
    #
    # synth = featherSynth5.FeatherSynth(AUDIO_OUT_PIN)
    synth = featherSynth5.FeatherSynth(
        i2s_bit_clock=AUDIO_OUT_I2S_BIT, i2s_word_select=AUDIO_OUT_I2S_WORD, i2s_data=AUDIO_OUT_I2S_DATA)
    synth.setVolume(0.1)

    waveIndex = 0
    waveName  = WAVEFORM_TYPES[waveIndex]
    displayWaveformName(display, waveName)
    synth.setWaveformSquare()

    lfoIndex = 0
    lfoMode = LFO_MODES[lfoIndex]
    displayLFOMode(display, lfoMode)

    dSleepMilliseconds = 0
    displayDelay(display, dSleepMilliseconds)

    # iter = 1
    wheelPositionLast = None

    # Play notes from a chromatic scale, as opposed to a continuous range of frequencies?
    # That is, integer MIDI numbers .vs. fractional.
    chromatic = True
    displayChromaticMode(display, chromatic)

    # Instructions here?
    display.setTextAreaR("Started!")

    wheelButtonHeld = False

    # ==== Main loop ===============================================================
    while True:

        # TODO: tidy up all this gesture-handling stuff

        # Rotary encoder wheel.
        # negate the position to make clockwise rotation positive
        position = -wheel.position
        if position != wheelPositionLast:
            wheelPositionLast = position

            # FIDME: even tho we limit the value we *use*, 
            # the hidden 'position' goes way out of bounds which works oddly. Fix!
            dSleepMilliseconds = clamp(position, 0, 100)

            # print(f"Wheel {position} - > d = {dSleepMilliseconds}")
            displayDelay(display, dSleepMilliseconds)

        wheelButtonPressed = not wheelButton.value
        if wheelButtonPressed and not wheelButtonHeld:
            chromatic = not chromatic
            displayChromaticMode(display, chromatic)
            print(f"chromatic: {chromatic}")
            wheelButtonHeld = True
        if not wheelButtonPressed:
            wheelButtonHeld = False


        changedWaveform = False
        lfoChanged = False

        gestureValue = 0
        if gestureSensor:
            gestureValue = gestureSensor.gesture()
        # print(f"gestureValue: {gestureValue}")

        if gestureValue == 1: # down
            waveIndex = waveIndex - 1
            if waveIndex < 0:
                waveIndex = len(WAVEFORM_TYPES)-1
            changedWaveform = True
        elif gestureValue == 2: # up
            waveIndex = waveIndex + 1
            if waveIndex >= len(WAVEFORM_TYPES):
                waveIndex = 0
            changedWaveform = True
        elif gestureValue == 3: # right
            lfoIndex = lfoIndex + 1
            if lfoIndex >= len(LFO_MODES):
                lfoIndex = 0
            lfoChanged = True
        elif gestureValue == 4: # left
            lfoIndex = lfoIndex - 1
            if lfoIndex < 0:
                lfoIndex = len(LFO_MODES)-1
            lfoChanged = True

        if changedWaveform:
            waveName = WAVEFORM_TYPES[waveIndex]
            print(f" -> Wave #{waveIndex}: {waveName}")
            displayWaveformName(display, waveName)
            # FIXME: a better way to do this?
            if waveIndex == 0:
                synth.setWaveformSquare()
            elif waveIndex == 1:
                synth.setWaveformSine()
            elif waveIndex == 2:
                synth.setWaveformSaw()

        if lfoChanged:
            lfoMode = LFO_MODES[lfoIndex]
            print(f" -> LFO #{lfoIndex}: {lfoMode}")
            displayLFOMode(display, lfoMode)

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


        # Get the two ranges, as available. 
        # (FIXME: Why is one always available, but the other is not? Different hardware.)
        # TODO: if not in a mode that uses this range, don't read it?
        #
        # r1 is the main ToF detector, used for main frequency.
        # r2 is the secondary ToF, used for LFO freq, and maybe other things.
        #
        r1 = tof_A.range
        # print(f"Range A: {r1}, range B: {r2}")

        if r1 > 0 and r1 < 1000:

            # (only read tof 2 if 1 is close)
            #
            r2 = tof_B.range    
            if r2 > 50 and r2 < 500:
                # TODO: REWORK THIS
                # - We do get readings farther out, to like XXXX at 2 feet, but will use the closer range.
                # TODO: Use values XXXX for now; tailor for trem/vib?
                # sometimes there seem to be false signals of 0, so toss them out.
                r2a = max(5, r2)
                # print(f"r2: {r2} -> r2a = {r2a}")

                # TODO: only set if r2 has *changed*? especially if we force the value to be an int.
                
                # if mode was changed, the "other" mode has already been cleared, so we are good to go.
                if lfoIndex == 1: # tremolo
                     # map to 8-16?
                    trem = map_and_scale(r2, 50, 500, 8, 16)
                    print(f"r2 {r2} -> trem {trem}")
                    synth.setTremolo(trem)
                elif lfoIndex == 2:
                    synth.setVibrato(r2a) # map to 4-10?

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

            # FIXME: this causes too much noise! synthio bug?
            # display.setTextAreaR(f"r1={r1}\nr2={r2}")

            synth.play(midiNote)
            time.sleep(dSleepMilliseconds/100)

        else: # no proximity detected
            synth.stop()

        # iter += 1


main() # :-)
