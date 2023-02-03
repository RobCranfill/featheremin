"""Make noises, based on a time-of-flight sensor.
    With VL53L4CD.
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

import feathereminDisplay

import adafruit_vl53l0x
import adafruit_vl53l4cd

# https://learn.adafruit.com/adafruit-apds9960-breakout/circuitpython
from adafruit_apds9960.apds9960 import APDS9960

# https://docs.circuitpython.org/projects/seesaw/en/latest/
from adafruit_seesaw import seesaw, rotaryio, digitalio

# GPIO pins used:
L0X_RESET_OUT = board.A0
AUDIO_OUT_PIN = board.A1

L4CD_ALTERNATE_I2C_ADDR = 0x31

ONE_OCTAVE = [440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 83.99, 830.61]


def makeWaveTables():
    # Generate one period of various waveforms.
    # TODO: Should there be an odd or even number of samples? we want to start and end with zeros, or at least some number.
    #
    length = 8000 // 440 + 1

    # this results in a fainter sound! why???
    # length = 16000 // 440 + 1

    sine_data = array.array("H", [0] * length)
    square_data = array.array("H", [0] * length)
    triangle_data = array.array("H", [0] * length)
    sawtooth_up_data = array.array("H", [0] * length)
    sawtooth_down_data = array.array("H", [0] * length)

    for i in range(length):
        sine_data[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
        if i < length/2:
            square_data[i] = 0
            triangle_data[i] = 2 * int(2**16 * i/length)
        else:
            square_data[i] = int(2 ** 16)-1
            triangle_data[i] = triangle_data[length-i-1]
        sawtooth_up_data[i] = int(i*2**16/length)
        sawtooth_down_data[i] = 2**16 - sawtooth_up_data[i] - 1

    # This is the nice dictionary we return:
    wave_tables = [
        ("sine", sine_data), 
        ("square", square_data), 
        ("triangle", triangle_data),
        ("saw up", sawtooth_up_data),
        ("saw down", sawtooth_down_data)]

    print(f"\nWave tables: {length} entries")
    print(f"{[w[0] for w in wave_tables]}")
    for i in range(length):
        print(f"({i},\t{sine_data[i]},\t{square_data[i]},\t{triangle_data[i]},\t{sawtooth_up_data[i]},\t{sawtooth_down_data[i]})")

    return wave_tables

    # end makeWaveTables()


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
    i2c.unlock()


def init_hardware():
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensors, gesture sensor, and display.

    None of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various harware items initialized.
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
            print(f"Found VL53L4CD at default address; now set to {hex(L4CD_ALTERNATE_I2C_ADDR)}")
            L4CD.set_address(L4CD_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
        except:
            print("No VL53L4CD?")
            sys.exit(1)


    # set non-default values - what?
    L4CD.inter_measurement = 0
    L4CD.timing_budget = 100

    # print("--------------------")
    # print("VL53L4CD:")
    # model_id, module_type = L4CD.model_info
    # print(f"    Model ID: 0x{model_id:0X}")
    # print(f"    Module Type: 0x{module_type:0X}")
    # print(f"    Timing Budget: {L4CD.timing_budget}")
    # print(f"    Inter-Measurement: {L4CD.inter_measurement}")
    # print("--------------------")

    L4CD.start_ranging()
    print("VL53L4CD init OK")

    # ----------------- VL53L0X time-of-flight sensor, part 2
    # Turn L0X back on and instantiate its object
    print("Turning VL53L0X back on...")
    L0X_reset.value = 1
    L0X = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
    print("VL53L0X init OK")


    # ----------------- APDS9960 gesture/proximity/color sensor 
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    apds.enable_gesture = True
    apds.rotation = 180


    # ----------------- OLED display
    oledDisp = feathereminDisplay.FeathereminDisplay()

    # Show it again? nah.
    # showI2Cbus()

    print("init_hardware OK!")
    return L0X, L4CD, apds, oledDisp


# Map the distance in millimeters to a sample rate in Hz
#
def rangeToNote(mm: int) -> float:

    sr = ONE_OCTAVE[mm // 50] * (8000 // 440)
    return sr


# --------------------------------------------------
# ------------------- begin main -------------------

print("\nHello, fetheremin!")

tof_L0X, tof_L4CD, gesture, display = init_hardware()

wave_tables = makeWaveTables()


# TODO: use or set quiescent_value ???
dac = audiopwmio.PWMAudioOut(AUDIO_OUT_PIN)

sleepTime = 0.2

nTries = 100
iter = 1
sampleRateLast = -1

useSineWave = True
wheelPositionLast = None

chromatic = False
display.setTextArea3(f"Chromatic: {chromatic}")

# chunkSleep = 0.1
# display.setTextArea2(f"Sleep: {chunkSleep:.2f}")
display.setTextArea2(f"Sleep: {0:.2f}")

waveIndex = 0
waveName  = wave_tables[waveIndex][0]
waveTable = wave_tables[waveIndex][1]

print(f"Wave #{waveIndex}: {waveName}")
display.setTextArea1(f"Waveform: {waveName}")

while True:

    g = gesture.gesture()
    if g == 1:
        waveIndex += 1
        if waveIndex >= len(wave_tables):
            waveIndex = 0
        waveName  = wave_tables[waveIndex][0]
        waveTable = wave_tables[waveIndex][1]
        print(f"Wave #{waveIndex}: {wave_tables[waveIndex][0]}")
        display.setTextArea1(f"Waveform: {waveName}")
    elif g == 2:
        waveIndex -= 1
        if waveIndex < 0:
            waveIndex = len(wave_tables) - 1
        waveName  = wave_tables[waveIndex][0]
        waveTable = wave_tables[waveIndex][1]
        print(f"Wave #{waveIndex}: {wave_tables[waveIndex][0]}")
        display.setTextArea1(f"Waveform: {waveName}")
    elif g == 3:
        chromatic = False
        print("left: chromatic off")
        display.setTextArea3(f"Chromatic: {chromatic}")
    elif g == 4:
        chromatic = True
        print("right: chromatic on")
        display.setTextArea3(f"Chromatic: {chromatic}")

    # Get the two ranges, if available. 
    # (Why is one always available, but the other is not?)
    #
    r1 = tof_L0X.range
    if tof_L4CD.data_ready:
        r2 = tof_L4CD.distance
        tof_L4CD.clear_interrupt()

    if r1 > 0 and r1 < 500:

        if chromatic:
            sampleRate = int(rangeToNote(r1))
            if sampleRate != sampleRateLast:

                dac.stop()

                print(f"#{iter}: {r1} mm -> {sampleRate} Hz {'sine' if useSineWave else 'square'}")

                waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)

                sampleRateLast = sampleRate
                dac.play(waveSample, loop=True)

                dSleep = r2/1000
                display.setTextArea2(f"Sleep: {dSleep:.2f}")
                time.sleep(dSleep)

        else: # "continuous", not chromatic; more "theremin-like"?
            
            # sampleRate = int(rangeToRate(r))
            sampleRate = int(30*r1 + 1000)

            # dac.stop()

            dSleep = r2/1000
            display.setTextArea2(f"Sleep: {dSleep:.2f}")
            time.sleep(dSleep)

            print(f"Cont: {waveName} #{iter}: {r1} mm -> {sampleRate} Hz; sleep {dSleep} ")

            waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)
            
            dac.play(waveSample, loop=True)

            # dac.stop()
            
    else:
        dac.stop()
        # pass
        # time.sleep(sleepTime)
        
    iter += 1
    # print("Done!")
