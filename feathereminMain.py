"""Make noises, based on various sensors including time-of-flight.
    robcranfill@gmail.com
"""
import array
import audiocore
import audiopwmio
import board
import busio
import digitalio as feather_digitalio
import math
import time
import sys

# Adafruit libraries - www.adafruit.com
import feathereminDisplay9341
import adafruit_vl53l0x
import adafruit_vl53l4cd
import adafruit_max9744
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel

import featherSynth5


# GPIO pins used:
L0X_RESET_OUT = board.D4
AUDIO_OUT_PIN = board.D5    # for PWM output
TFT_DISPLAY_CS = board.A2
TFT_DISPLAY_DC = board.A0
TFT_DISPLAY_RESET = board.A1

L4CD_ALTERNATE_I2C_ADDR = 0x31

INITIAL_AMP_VOLUME = 10 # 25 is max for 20W amp and 3W 4 ohm speaker with 12v to amp.


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()


def init_hardware() -> list(adafruit_vl53l0x.VL53L0X,   # 1st ToF sensor
                            adafruit_vl53l4cd.VL53L4CD, # 2nd ToF sensor
                            APDS9960,                   # gesture sensor
                            feathereminDisplay9341.FeathereminDisplay9341, # our display object
                            adafruit_max9744.MAX9744,   # amplifier, or None
                            rotaryio.IncrementalEncoder, # rotary encoder
                            digitalio.DigitalIO,        # pushbutton in rotary encoder
                            neopixel.NeoPixel           # neopixel in rotary encoder
                            ):
    
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensors, gesture sensor, display, and amp (if attached).

    Mostly none of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various hardware items initialized.
    """

    # Easist way to init I2C on a Feather:
    i2c = board.STEMMA_I2C()

    # For fun
    showI2Cbus()

    # ----------------- VL53L0X time-of-flight sensor 
    # We will finish setting this sensor up 
    # *after* we turn it off an init the other ToF sensor.
    
    # Turn off the ToF sensor - take XSHUT pin low
    print("Turning off VL53L0X...")
    L0X_reset = feather_digitalio.DigitalInOut(L0X_RESET_OUT)
    L0X_reset.direction = feather_digitalio.Direction.OUTPUT
    L0X_reset.value = 0
    # VL53L0X sensor is now turned off

    # ----------------- VL53L4CD time-of-flight sensor
    # L4CD ToF
    # First, see if it's there with the new address (left over from a previous run).
    # If so, we don't need to re-assign it.
    try:
        L4CD = adafruit_vl53l4cd.VL53L4CD(i2c, address=L4CD_ALTERNATE_I2C_ADDR)
        print(f"Found VL53L4CD at {hex(L4CD_ALTERNATE_I2C_ADDR)}; OK")
    except:
        print(f"Did not find VL53L4CD at {hex(L4CD_ALTERNATE_I2C_ADDR)}, trying default....")
        try:
            L4CD = adafruit_vl53l4cd.VL53L4CD(i2c)
            print(f"Found VL53L4CD at default address; setting to {hex(L4CD_ALTERNATE_I2C_ADDR)}...")
            L4CD.set_address(L4CD_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
            print("VL53L4CD set_address OK")
        except:
            print("**** No VL53L4CD?")
            L4CD = None
    finally:
        # # set non-default values?
        L4CD.inter_measurement = 0
        L4CD.timing_budget = 100
        L4CD.start_ranging()

        # print("--------------------")
        # print("VL53L4CD:")
        # model_id, module_type = L4CD.model_info
        # print(f"    Model ID: 0x{model_id:0X}")
        # print(f"    Module Type: 0x{module_type:0X}")
        # print(f"    Timing Budget: {L4CD.timing_budget}")
        # print(f"    Inter-Measurement: {L4CD.inter_measurement}")
        # print("--------------------")
        print("VL53L4CD init OK")

    # ----------------- VL53L0X time-of-flight sensor, part 2
    # Turn L0X back on and instantiate its object
    print("Turning VL53L0X back on...")
    L0X_reset.value = 1
    try:
        L0X = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
        print("VL53L0X init OK")
    except:
        print("**** No VL53L0X? Continuing....")

    # Show bus again?
    # showI2Cbus()

    # ----------------- APDS9960 gesture/proximity/color sensor
    apds = None
    try:
        apds = APDS9960(i2c)
        apds.enable_proximity = True
        apds.enable_gesture = True
        apds.rotation = 180
        print("APDS9960 init OK")
    except:
        print("**** No APDS9960? Continuing....")

    # ----------------- Our display object
    display = feathereminDisplay9341.FeathereminDisplay9341(TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)
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
    ss = seesaw.Seesaw(i2c, addr=0x36)
    seesaw_v = (ss.get_version() >> 16) & 0xFFFF
    # print(f"Found product {seesaw_v}")
    if seesaw_v != 4991:
        print("**** Wrong Rotary encoder firmware loaded?  Expected 4991")
        # what are we supposed to do about this??
    encoder = rotaryio.IncrementalEncoder(ss)

    # the "button" that is got by pushing down on the encoder wheel
    ss.pin_mode(24, ss.INPUT_PULLUP)
    wheel_button = digitalio.DigitalIO(ss, 24)
    # button_held = False

    # TODO: tried to do something with the Neopixel but haven't figured anything out yet. :-/
    pixel = neopixel.NeoPixel(ss, 6, 1)
    # pixel.brightness = 0.1
    pixel.fill(0x004000) # green for go!
    print("Rotary encoder init OK")


    print("\ninit_hardware OK!\n")
    return L0X, L4CD, apds, display, amp, encoder, wheel_button, pixel

# TODO: this is f*ed up
# in: the gesture sensor, current wave index, chromatic flag
# returns: new wave index, new chromatic flag
def handleGesture(gSensor, pWaveIndex, pChromatic):

    gestureValue = gSensor.gesture()
    if gestureValue == 0:
        return pWaveIndex, pChromatic

    if gestureValue == 1: # down (in default orientation)
        pWaveIndex += 1
        if pWaveIndex >= len(wave_tables):
            pWaveIndex = 0
    elif gestureValue == 2: # up
        pWaveIndex -= 1
        if pWaveIndex < 0:
            pWaveIndex = len(wave_tables) - 1

    elif gestureValue == 3: # right
        pChromatic = False
        print("right: chromatic off")
        # display.setTextArea3(f"Chromatic: {chromatic}")
        # pDisplay.setTextAreaL("Continuous")
    elif gestureValue == 4: # left
        pChromatic = True
        print("left: chromatic on")

    return pWaveIndex, pChromatic


def displayChromaticMode(disp, chromaticFlag):
    disp.setTextAreaL("Chromatic" if chromaticFlag else "Continuous")

def displayDelay(disp, sleepMS):
    disp.setTextArea2(f"Sleep: {sleepMS} ms")

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
    tof_L0X, tof_L4CD, gesture, display, amp, wheel, wheelButton, wheelLED = init_hardware()

    # NEW SYNTH STUFF
    synth = featherSynth5.FeatherSynth(AUDIO_OUT_PIN)
    waveIndex = 0
    waveName  = "SIO: Sine"
    sioSineFlag = False

    dSleepMilliseconds = 0

    iter = 1
    sampleRateLast = -1

    wheelPositionLast = None

    print(f"Wave #{waveIndex}: {waveName}")
    displayDelay(display, dSleepMilliseconds)
    # FIXME: ad hoc
    display.setTextArea1(f"Waveform: {waveName}")
    display.setTextArea3("")

    # Play notes from a chromatic scale, as opposed to a continuous range of frequencies.
    # That is, integer MIDI numbers .vs. fractional.
    #
    chromatic = True

    displayChromaticMode(display, chromatic)

    # Instructions here?
    display.setTextAreaR("You are\nmahvelous!")

    wheelButtonHeld = False

    # ==== Main loop ===============================================================
    while True:

        # Rotary encoder wheel.
        # negate the position to make clockwise rotation positive
        position = -wheel.position
        if position != wheelPositionLast:
            wheelPositionLast = position
            dSleepMilliseconds = max(min(position, 100), 0)
            print(f"Wheel {position} - > d = {dSleepMilliseconds}")
            displayDelay(display, dSleepMilliseconds)

        wheelButtonPressed = not wheelButton.value
        if wheelButtonPressed and not wheelButtonHeld:
            chromatic = not chromatic
            displayChromaticMode(display, chromatic)
            print(f"chromatic: {chromatic}")
            wheelButtonHeld = True
        if not wheelButtonPressed:
            wheelButtonHeld = False

        # FIXME: this is all f*ed up
        # Gesture sensor?
        lastWaveIndex, lastChromatic = waveIndex, chromatic
        waveIndex, chromatic = handleGesture(gesture, waveIndex, chromatic)
        if waveIndex != lastWaveIndex:

            sioSineFlag = not sioSineFlag
            # display.setTextAreaL(f"{'SIO: Sine' if sioSineFlag else 'SIO: Saw'}")
            display.setTextAreaL(f"SIO: Sine? {sioSineFlag}")

        if chromatic != lastChromatic:
            display.setTextAreaL(f"{'Chromatic' if chromatic else 'Continuous'}")


        # Get the two ranges, as available. 
        # (FIXME: Why is one always available, but the other is not? Different hardware.)
        #
        r1 = tof_L0X.range
        r2 = 0
        if tof_L4CD.data_ready:

            r2 = max(0, tof_L4CD.distance - 10)
            if r2 > 50:
                r2 = 0
            # print(f"r2 = {r2}")
            # must do this to get another reading
            tof_L4CD.clear_interrupt()

        if r1 > 0 and r1 < 1000:

            midiNote = r1 / 4
            if midiNote > 127:
                midiNote = 127

            if chromatic:
                midiNote = int(midiNote)

            else: # "continuous", not chromatic; more "theremin-like"?
                pass

            print(f"SIO: midiNote {midiNote} ")
            synth.play(midiNote)
            time.sleep(dSleepMilliseconds/100)

        else: # no proximity detected
            synth.stop()

        iter += 1


main() # :-)
