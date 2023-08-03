##
## test_2_L0X_testbed
## goofin around
##

import board
import adafruit_vl53l0x as vl32l0x
import digitalio as feather_digitalio
import time

# our synth object, or one of them:
import featherSynth6 as fSynth


# GPIO pins
# The GPIO pin we use to turn the 'primary' ("A") ToF sensor off,
# so we can re-program the address of the secondary one.
L0X_A_RESET_OUT = board.D4

# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11


# I2C addresses - VL53L0X defaults to 0x29
# we will change the secondary sensor to this address
L0X_B_ALTERNATE_I2C_ADDR = 0x30


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"  {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()


""" Initialize the ToF sensors
"""
def init_sensors(i2c) -> tuple[vl32l0x.VL53L0X, vl32l0x.VL53L0X]:

    # ----------------- 'Primary' VL53L0X time-of-flight sensor 
    # We have wired a GPIO line to this sensor so we can temporarily turn it off.
    # We will finish setting this sensor up after we init the 'secondary' ToF sensor.

    # Turn off the ToF sensor - take XSHUT pin low
    print("Turning off primary VL53L0X...")
    L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
    L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
    L0X_A_reset.value = False
    # primary VL53L0X sensor is now turned off
    print("After turning off primary: ")
    showI2Cbus()


    # ----------------- 'Secondary' VL53L0X time-of-flight sensor
    # 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
    # First, see if it's there with the new address (left over from a previous run).
    # If so, we don't need to re-assign it.
    try:
        L0X_B = vl32l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
        print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
    except:
        print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
        try:
            L0X_B = vl32l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
            print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
            L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
            print("VL53L0X set_address OK")

            print("secondary VL53L0X init OK")
        except:
            print("**** No secondary VL53L0X?")
            L0X_B = None


    # ----------------- Primary sensor, part 2
    # Turn it back on and instantiate its object
    print("Turning primary VL53L0X back on...")
    L0X_A_reset.value = True
    try:
        L0X_A = vl32l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
        print("'Primary' VL53L0X init OK")

        # a higher speed but less accurate timing budget of 20ms:
        L0X_A.measurement_timing_budget = 20000
    except:
        print("**** No primary VL53L0X? Continuing....")

    return L0X_A, L0X_B

    # end init_hardware


def init_audio():

    stereo = True

    # synth = featherSynth5.FeatherSynth(AUDIO_OUT_PIN)
    synth = fSynth.FeatherSynth(stereo,
                                i2s_bit_clock=AUDIO_OUT_I2S_BIT, 
                                i2s_word_select=AUDIO_OUT_I2S_WORD, 
                                i2s_data=AUDIO_OUT_I2S_DATA)
    
    return synth


# main

i2c = board.STEMMA_I2C()

L0X_A, L0X_B = init_sensors(i2c)

synth = init_audio()

print("Bus to start: ")
showI2Cbus()

# synth.test(5)
synth.test_phat_2()
while True:
    pass

while True:
    r1 = L0X_A.range
    r2 = L0X_B.range

    print(f"({r1}, {r2})")
    time.sleep(.5)
