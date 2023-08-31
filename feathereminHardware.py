import board
import gc

import digitalio as feather_digitalio

import featherSynth5 as fSynth


#############################################################3
# Things to do
##############
# Do we need to 'deinit' things? Which things?? Might not be a bad idea!
# Such as the GPIOs, display, sensors
# See '__del__' method below.

# Adafruit hardware libraries - www.adafruit.com
import adafruit_vl53l0x
from adafruit_apds9960.apds9960 import APDS9960

# The L0X defaults to I2C 0x29; we have two, one of which we will re-assign to this address.
L0X_B_ALTERNATE_I2C_ADDR = 0x30


# LCD display
USE_SIMPLE_DISPLAY = True
if USE_SIMPLE_DISPLAY:
    import feathereminDisplay3 as fDisplay
else:
    import feathereminDisplay2 as fDisplay


def showI2Cbus(i2c):
    # i2c = board.I2C()
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

    Returns: Nothing. Call getHardwareItems() to get the list of hardware objects.
    """

    # TODO: use named params
    def __init__(self,
                display_cs_pin, display_dc_pin, display_reset_pin,
                audio_out_i2s_bit_pin, audio_out_i2s_word_pin, audio_out_i2s_data_pin,
                l0x_a_reset_out_pin
                ):

        # Easist way to init I2C on a Feather
        self._i2c = None
        try:
            self._i2c = board.STEMMA_I2C()
        except:
            print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")
            # return tuple() # fail fast?

        # For fun
        showI2Cbus(self._i2c)

        # ----------------- Our display object - do this early so we can show errors?
        if USE_SIMPLE_DISPLAY:
            self._display = fDisplay.FeathereminDisplay(180, display_cs_pin, display_dc_pin, display_reset_pin, 4)
        else:
            self._display = fDisplay.FeathereminDisplay(180, False, display_cs_pin, display_dc_pin, display_reset_pin)
        print("Display init OK")


        # ----------------- 'A' VL53L0X time-of-flight sensor
        # 'A' ToF - this has its XSHUT pin wired to GPIO {L0X_A_RESET_OUT}.
        # We will finish setting this sensor up 
        # *after* we turn it off and init the 'B' ToF sensor.
        
        # Turn off this ToF sensor - take XSHUT pin low.
        #
        print("Turning off 'A' VL53L0X...")

        # We keep this as an instance var so we can de-init it later.
        self._L0X_A_reset = feather_digitalio.DigitalInOut(l0x_a_reset_out_pin)
        self._L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
        self._L0X_A_reset.value = False

        # 'A' VL53L0X sensor is now turned off
        showI2Cbus(self._i2c)


        # ----------------- 'B' VL53L0X time-of-flight sensor
        # 'B' ToF - the one that *doesn't* have its XSHUT pin wired up, so is always 'on'.
        # First, see if it's there already with the non-default address (left over from a previous run).
        # If so, we don't need to re-assign it.
        try:
            self._L0X_B = adafruit_vl53l0x.VL53L0X(self._i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
            print(f"Found 'B' VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
        except:
            print(f"Did not find 'B' VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
            try:
                # Try at the default address
                self._L0X_B = adafruit_vl53l0x.VL53L0X(self._i2c)  # also performs VL53L0X hardware check
                print(f"Found 'B' VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
                self._L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
                print("VL53L0X 'B' set_address OK")

                # Set params for the sensor
                # The default timing budget is 33ms (measurement_timing_budget = 33000),
                # a good compromise of speed and accuracy.
                # For example, a higher speed but less accurate timing budget of 20ms (20000),
                # or a slower but more accurate timing budget of 200ms (2000)
                #
                self._L0X_B.measurement_timing_budget = 33000

                print("'B' VL53L0X init OK")
            except Exception as e:
                print(f"**** Caught exception: {e}")
                print("**** No 'B' VL53L0X?")
                self._L0X_B = None


        # ----------------- VL53L0X time-of-flight sensor, part 2
        # Turn L0X back on and instantiate its object
        print("Turning 'A' VL53L0X back on...")
        self._L0X_A_reset.value = True

        self._L0X_A = None
        try:
            self._L0X_A = adafruit_vl53l0x.VL53L0X(self._i2c)  # also performs VL53L0X hardware check

            # Set params for the sensor
            self._L0X_A.measurement_timing_budget = 33000

            print("'A' VL53L0X init OK")
        except:
            print("**** No 'A' VL53L0X? Continuing....")

        # Show bus again?
        showI2Cbus(self._i2c)


        # ----------------- APDS9960 gesture/proximity/color sensor
        self._apds = None
        try:
            self._apds = APDS9960(self._i2c)
            self._apds.enable_proximity = True
            self._apds.enable_gesture = True
            self._apds.rotation = 90
            print("APDS9960 init OK")
        except:
            print("**** No APDS9960? Continuing....")


        # My "synthezier" object that does the stuff that I need.
        #
        USE_STEREO = True
        self._synth = fSynth.FeatherSynth(USE_STEREO,
                                    i2s_bit_clock = audio_out_i2s_bit_pin, 
                                    i2s_word_select = audio_out_i2s_word_pin, 
                                    i2s_data = audio_out_i2s_data_pin)
        self._synth.setVolume(0.75)


        showMem()
        print("")
        print("init_hardware OK!")
        print("")

        # end __init__


    def getHardwareItems(self) -> Tuple[
                        adafruit_vl53l0x.VL53L0X,       # 'A' ToF sensor
                        adafruit_vl53l0x.VL53L0X,       # 'B' ToF sensor
                        APDS9960,                       # gesture sensor
                        fDisplay.FeathereminDisplay,    # our display object
                        fSynth.FeatherSynth             # our synth thingy
                        ]:
        '''
        Return a tuple of all the hardare objects.

        '''
        return self._L0X_A, self._L0X_B, self._apds, self._display, self._synth


    def __del__(self):
        ''' Destructor
        '''

        # de-init the synth?
        # self._synth. ??


        # release the I2C bus
        self._i2c.deinit()

        # release the hardware pin
        self._L0X_A_reset.deinit()

        self._L0X_A = None
        self._L0X_B = None
        self._apds = None
        self._display = None
        print("\nHardware object destroyed!\n")
