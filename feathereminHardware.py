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

# # Other Featheremin modules
# import featherSynth5 as fSynth
# import gestureMenu


# GPIO pins used:
# The GPIO pin we use to turn the 'primary' ("A") ToF sensor off,
# so we can re-program the address of the secondary one.
L0X_A_RESET_OUT = board.D4


TFT_DISPLAY_CS    = board.A2
TFT_DISPLAY_DC    = board.A0
TFT_DISPLAY_RESET = board.A1

# The L0X defaults to I2C 0x29; we have two, one of which we will re-assign to this address.
L0X_B_ALTERNATE_I2C_ADDR = 0x30

# LCD display
USE_SIMPLE_DISPLAY = True
if USE_SIMPLE_DISPLAY:
    import feathereminDisplay3 as fDisplay
else:
    import feathereminDisplay2 as fDisplay

# ROTARY_ENCODER_I2C_ADDR = 0x36
# SEE_SAW_BUTTON_PIN_WTF = 24  # FIXME: wtf is this magic number?
# INITIAL_20W_AMP_VOLUME = 10 # 25 is max for 20W amp and 3W 4 ohm speaker with 12v to amp.


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()

def showMem():
    gc.collect()
    print(f"Free memory: {gc.mem_free()}")


class FeatereminHardware:
    """Initialize all hardware items.

    Namely, the I2C bus, Time of Flight sensors, gesture sensor, display, and amp (if attached).

    Mostly none of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various hardware items initialized.
    """

    def __init__(self):

# was:
# def init_hardware() -> tuple[adafruit_vl53l0x.VL53L0X,   # 'A' ToF sensor
#                             adafruit_vl53l0x.VL53L0X,    # 'B' ToF sensor
#                             APDS9960,                    # gesture sensor
#                             fDisplay.FeathereminDisplay, # our display object
#                             adafruit_max9744.MAX9744,    # big amplifier, or None
#                             rotaryio.IncrementalEncode,  # rotary encoder
#                             digitalio.DigitalIO,         # pushbutton in rotary encoder
#                             neopixel.NeoPixel            # neopixel in rotary encoder
#                             ]:


        # supervisor.reload()

        # Easist way to init I2C on a Feather:
        try:
            i2c = board.STEMMA_I2C()
        except:
            print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")
            # return tuple()

        # For fun
        showI2Cbus()

        if USE_SIMPLE_DISPLAY:
        # ----------------- Our display object - do this early so we can show errors?
            self._display = fDisplay.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET, 4)
        else:
            self._display = fDisplay.FeathereminDisplay(180, False, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)

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
            self._L0X_B = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
            print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
        except:
            print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
            try:
                # Try at the default address
                self._L0X_B = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
                print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
                self._L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
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
                self._L0X_B = None


        # ----------------- VL53L0X time-of-flight sensor, part 2
        # Turn L0X back on and instantiate its object
        print("Turning 'primary' VL53L0X back on...")
        L0X_A_reset.value = True
        self._L0X_A = None
        try:
            self._L0X_A = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
            # Set params for the sensor?

            print("'Primary' VL53L0X init OK")
        except:
            print("**** No primary VL53L0X? Continuing....")

        # Show bus again?
        showI2Cbus()


        # ----------------- APDS9960 gesture/proximity/color sensor
        self._apds = None
        try:
            self._apds = APDS9960(i2c)
            self._apds.enable_proximity = True
            self._apds.enable_gesture = True
            self._apds.rotation = 90
            print("APDS9960 init OK")
        except:
            print("**** No APDS9960? Continuing....")


        # # ------------------ MAX9744 amp, if any
        # # TODO: merge this into the Synth object? Or at least hand it to that object to use?
        # amp = None
        # # try:
        # #     amp = adafruit_max9744.MAX9744(i2c)
        # #     amp.volume = INITIAL_20W_AMP_VOLUME
        # #     print("MAX9744 amp init OK")
        # # except Exception as e:
        # #     print(f"No MAX9744 amplifier found: '{e}' - OK?")
        # #     amp = None

        # # ------------------ Rotary encoder
        # encoder, wheel_button, pixel = None, None, None
        # # try:
        # #     ss = seesaw.Seesaw(i2c, addr=ROTARY_ENCODER_I2C_ADDR)
        # #     seesaw_v = (ss.get_version() >> 16) & 0xFFFF
        # #     # print(f"Found product {seesaw_v}")
        # #     if seesaw_v != 4991:
        # #         print("Wrong rotary encoder firmware version? Continuing...")
        # #         # what are we supposed to do about this??
        # #     encoder = rotaryio.IncrementalEncoder(ss)
        # #
        # #     # the "button" that is got by pushing down on the encoder wheel
        # #     ss.pin_mode(SEE_SAW_BUTTON_PIN_WTF, ss.INPUT_PULLUP)
        # #     wheel_button = digitalio.DigitalIO(ss, 24)
        # #
        # #     # TODO: tried to do something with the Neopixel but haven't figured anything out yet. :-/
        # #     pixel = neopixel.NeoPixel(ss, 6, 1)
        # #   
        # #     pixel.fill(0x000100) # very light green - for go!
        # #     # pixel.brightness = 0.1
        # #
        # #     print("Rotary encoder init OK")
        # #
        # # except:
        # #     print(f"\n**** No rotary encoder at I2C {hex(ROTARY_ENCODER_I2C_ADDR)}? OK\n")


        showMem()
        print("")
        print("init_hardware OK!")
        print("")

        # return L0X_A, L0X_B, apds, display, amp, encoder, wheel_button, pixel
        
        # end __init__


    def getHardwareItems(self): # ->
                    # tuple[
                    #     adafruit_vl53l0x.VL53L0X,   # 'A' ToF sensor
                    #     adafruit_vl53l0x.VL53L0X,    # 'B' ToF sensor
                    #     APDS9960,                    # gesture sensor
                    #     fDisplay.FeathereminDisplay  # our display object
                    #     ]:
    
        return self._L0X_A, self._L0X_B, self._apds, self._display
