# simple code to test sound generation with ToF sensors
# robcranfill@gmail.com

import adafruit_vl53l0x as vl53l0x
import board
import digitalio as feather_digitalio
import time
import math

import featherSynth5 as fSynth

RANGE_THRESH = 8000

# The L0X defaults to I2C 0x29; we have two, one of which we will re-assign to this address.
L0X_A_DEFAUJLT_I2C_ADDR = 0x29
L0X_B_ALTERNATE_I2C_ADDR = 0x30
L0X_A_RESET_OUT = board.D4

# for I2S audio out
AUDIO_OUT_I2S_BIT  = board.D9
AUDIO_OUT_I2S_WORD = board.D10
AUDIO_OUT_I2S_DATA = board.D11

# assume the I2C addresses have been set?
def init_hardware() -> tuple[vl53l0x.VL53L0X, vl53l0x.VL53L0X]:

    i2c = board.STEMMA_I2C()
    showI2Cbus()

    L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
    L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT

    # ----------------- VL53L4CD time-of-flight sensor
    # 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
    # First, see if it's there with the new address (left over from a previous run).
    # If so, we don't need to re-assign it.
    try:
        L0X_B = vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
        print(f"'Secondary' VL53L0X init at {hex(L0X_B_ALTERNATE_I2C_ADDR)} OK")
    except Exception as e:
        print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)} ({e})")
        print("Turning off primary VL53L0X?")
        L0X_A_reset.value = False
        # VL53L0X sensor is now turned off
        showI2Cbus()

        try:
            L0X_B = vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
            print(f"Found' VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
            L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
            print("VL53L0X set_address OK")
        except:
            L0X_B = None
    
    # 'Primary' sensor
    try:
        L0X_A_reset.value = True
        L0X_A = vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
        print(f"'Primary' VL53L0X init at {hex(L0X_A_DEFAUJLT_I2C_ADDR)} OK")
    except Exception as e:
        print(f"'Primary' VL53L0X failed init! {e}")
        L0X_A = None

    L0X_A_reset.deinit()

    return L0X_A, L0X_B


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
        i2c.unlock()

def map_and_scale(inValue, lowIn, highIn, lowOut, highOut):
    frac = (inValue-lowIn)/(highIn-lowIn)
    return lowOut + frac * (highOut-lowOut)

# CP doesn't have math.isclose() !
def isclose(x1, x2):
    return (x1-x2) < 0.00001

def test_map(t, lowIn, highIn, lowOut, highOut, expected):
    x = map_and_scale(t, lowIn, highIn, lowOut, highOut)
    print(f"test({t}, {lowIn}, {highIn}, {lowOut}, {highOut} = {x} ? (expect {expected})")
    # if not math.isclose(x, expected):
    if not isclose(x, expected):
        raise Exception(f"Test fails! {x/expected}")

def test_mapping():
    test_map(1, 0, 10, 0, 100, 10.0)
    test_map(1, 0, 10, 100, 200, 110.0)
    print("mapping tests OK!")

# -------------------- main
tof_A, tof_B = init_hardware()
if tof_A is None or tof_B is None:
     print("Nope!")
     while True:
          pass

synth = fSynth.FeatherSynth(i2s_bit_clock=AUDIO_OUT_I2S_BIT, i2s_word_select=AUDIO_OUT_I2S_WORD, i2s_data=AUDIO_OUT_I2S_DATA)
synth.setVolume(0.1)

print("HW init OK?")

# test_mapping()
# while True:
#     pass

droneStarted = False
while True:

        # range, in millimeters, more or less
        r1 = tof_A.range
        if r1 > RANGE_THRESH:
             r1 = -1
        r2 = tof_B.range
        if r2 > RANGE_THRESH:
            r2 = -1
        # print(f"Range A: {r1}; Range B: {r2}")

        # synth.play(42)
        # synth.test(5)

        if r1 > 0 and r2 > 0:
            f1 = map_and_scale(r1, 0, 2000, 1000, 20000)
            f2 = map_and_scale(r2, 0, 2000, 1000, 20000)
            print(f"done {f1}/{f2}")
            if not droneStarted:
                synth.startDrone(f1, f2)
                droneStarted = True
            else:
                synth.drone(f1, f2)
        else:
            synth.stopDrone()
            droneStarted = False

        time.sleep(.1)

