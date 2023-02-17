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

import feathereminDisplay9341

import adafruit_vl53l0x
import adafruit_vl53l4cd

import adafruit_max9744

# https://learn.adafruit.com/adafruit-apds9960-breakout/circuitpython
from adafruit_apds9960.apds9960 import APDS9960

# https://docs.circuitpython.org/projects/seesaw/en/latest/
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel


TEST_WHEEL_MODE = True

# GPIO pins used:
L0X_RESET_OUT = board.D4
AUDIO_OUT_PIN = board.D5

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

    if False:
        print(f"\nWave tables: {length} entries:")
        print(f"{[w[0] for w in wave_tables]}")
        for i in range(length):
            print(
                f"({i}," +
                f"\t{sine_data[i]:5},\t{square_data[i]:5},\t{triangle_data[i]:5}," +
                f"\t{sawtooth_up_data[i]:5},\t{sawtooth_down_data[i]:5})")

    return wave_tables

    # end makeWaveTables()


def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
    i2c.unlock()


def init_hardware():
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensors, gesture sensor, display, and amp (if attached).

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

            # # set non-default values?
            # L4CD.inter_measurement = 0
            # L4CD.timing_budget = 100

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

        except:
            print("**** No VL53L4CD?")
            # sys.exit(1)
            L4CD = None


    # ----------------- VL53L0X time-of-flight sensor, part 2
    # Turn L0X back on and instantiate its object
    print("Turning VL53L0X back on...")
    L0X_reset.value = 1
    L0X = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
    print(f"VL53L0X init OK ({L0X})")


    # ----------------- APDS9960 gesture/proximity/color sensor
    apds = None
    try:
        apds = APDS9960(i2c)
        apds.enable_proximity = True
        apds.enable_gesture = True
        apds.rotation = 180
    except:
        print("**** No APDS9960? Continuing....")

    # ----------------- OLED display
    oledDisp = feathereminDisplay9341.FeathereminDisplay9341()

    # Show it again? nah.
    # showI2Cbus()


    # ------------------ MAX9744 amp, if any
    amp = None
    try:
        amp = adafruit_max9744.MAX9744(i2c)
        amp.volume = 25 # OK for small 4 ohm, 3W speaker
    except:
        print("**** No MAX9744 found; continuing....")


    # ------------------ Rotary encoder
    ss = seesaw.Seesaw(i2c, addr=0x36)
    seesaw_v = (ss.get_version() >> 16) & 0xFFFF
    print(f"Found product {seesaw_v}")
    if seesaw_v != 4991:
        print("**** Wrong Rotary encoder firmware loaded?  Expected 4991")
    encoder = rotaryio.IncrementalEncoder(ss)

    # pixel = neopixel.NeoPixel(ss, 6, 1)
    # pixel.brightness = 1.0


    print("init_hardware OK!")
    return L0X, L4CD, apds, oledDisp, amp, encoder


# Map the distance in millimeters to a sample rate in Hz
#
def rangeToNote(mm: int) -> float:

    sr = ONE_OCTAVE[mm // 50] * (8000 // 440)
    return sr


# in: gestureValue, wave_tables...
# uses: wave_tables
# returns: pWaveIndex, wave_table, wave_name, chrom_flag
# sets: textarea1, textareaL
def handleGesture(gestureValue, pWaveIndex, pChromFlag):

    chrom_flag = pChromFlag
    wave_name  = wave_tables[pWaveIndex][0]
    wave_table = wave_tables[pWaveIndex][1]

    if gestureValue == 1: # down (in default orientation)
        pWaveIndex += 1
        if pWaveIndex >= len(wave_tables):
            pWaveIndex = 0
        wave_name  = wave_tables[pWaveIndex][0]
        wave_table = wave_tables[pWaveIndex][1]
        print(f"Wave #{pWaveIndex}: {wave_name}")
        display.setTextArea1(f"Waveform: {wave_name}")
    
    elif gestureValue == 2: # up
        pWaveIndex -= 1
        if pWaveIndex < 0:
            pWaveIndex = len(wave_tables) - 1
        wave_name  = wave_tables[pWaveIndex][0]
        wave_table = wave_tables[pWaveIndex][1]
        print(f"Wave #{pWaveIndex}: {wave_name}")
        display.setTextArea1(f"Waveform: {wave_name}")

    elif gestureValue == 3: # right
        chrom_flag = False
        print("right: chromatic off")
        # display.setTextArea3(f"Chromatic: {chromatic}")
        display.setTextAreaL(f"{'Chromatic' if chromatic else 'Continuous'}")

    elif gestureValue == 4: # left
        chrom_flag = True
        print("left: chromatic on")
        # display.setTextArea3(f"Chromatic: {chromatic}")
        display.setTextAreaL(f"{'Chromatic' if chromatic else 'Continuous'}")

    return pWaveIndex, wave_table, wave_name, chrom_flag


# --------------------------------------------------
# ------------------- begin main -------------------

print("\nHello, fetheremin!")

tof_L0X, tof_L4CD, gesture, display, amp, wheel = init_hardware()


wave_tables = makeWaveTables()


# TODO: use or set quiescent_value ???
dac = audiopwmio.PWMAudioOut(AUDIO_OUT_PIN)

sleepTime = 0.2
dSleep = 0

iter = 1
sampleRateLast = -1

wheelPositionLast = None

chromatic = False
# display.setTextArea3(f"{'Chromatic' if chromatic else 'Continuous'}")
display.setTextArea3("")


# chunkSleep = 0.1
# display.setTextArea2(f"Sleep: {chunkSleep:.2f}")
display.setTextArea2(f"Sleep: {0:.2f}")

waveIndex = 0
waveName  = wave_tables[waveIndex][0]
waveTable = wave_tables[waveIndex][1]

print(f"Wave #{waveIndex}: {waveName}")
display.setTextArea1(f"Waveform: {waveName}")


while True:

    # negate the position to make clockwise rotation positive
    position = - wheel.position
    if position != wheelPositionLast:
        wheelPositionLast = position
        print(f"Wheel: {position}")

    if gesture: # if we have a sensor; TODO: not necessary to check?
        gx = gesture.gesture()
        if gx > 0:
            waveIndex, waveTable, waveName, chromatic = handleGesture(gx, waveIndex, chromatic)

    # Get the two ranges, if available. 
    # (TODO: Why is one always available, but the other is not?)
    #
    r1 = tof_L0X.range
    r2 = 0
    if tof_L4CD and tof_L4CD.data_ready:
        r2 = tof_L4CD.distance
        if r2 > 50:
            r2 = 0
        # print(f"r2 = {r2}")

        dSleep = r2/100
        display.setTextArea2(f"Sleep: {dSleep:.2f}")
            
        tof_L4CD.clear_interrupt()

    if r1 > 0 and r1 < 500:

        if chromatic:
            sampleRate = int(rangeToNote(r1))
            if sampleRate != sampleRateLast:

                sampleRateLast = sampleRate

                print(f"Chrom: {waveName} #{iter}: {r1} mm -> {sampleRate} Hz; sleep {dSleep} ")



                dac.stop()
                waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)
                dac.play(waveSample, loop=True)
                time.sleep(dSleep)

        else: # "continuous", not chromatic; more "theremin-like"?
            
            # TODO: this sleeps, then plays, as opposed to the other way round. Why?

            # sampleRate = int(rangeToRate(r))
            sampleRate = int(30*r1 + 1000)

            # dac.stop()

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
