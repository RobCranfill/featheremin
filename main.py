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

import feathereminDisplay9341
import adafruit_vl53l0x
import adafruit_vl53l4cd
import adafruit_max9744
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel


# GPIO pins used:
L0X_RESET_OUT = board.D4
AUDIO_OUT_PIN = board.D5

L4CD_ALTERNATE_I2C_ADDR = 0x31

ONE_OCTAVE = [440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 83.99, 830.61]
INITIAL_AMP_VOLUME = 10 # 25 is max for 20W amp and 3W 4 ohm speaker with 12v to amp.

def makeWaveTables():
    # Generate one period of various waveforms.
    # TODO: Should there be an odd or even number of samples? we want to start and end with zeros, or at least some number.
    #
    # originally 8K
    length = 16000 // 440 + 1

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

    # print(f"\nWave tables: {length} entries:")
    # print(f"{[w[0] for w in wave_tables]}")
    # for i in range(length):
    #     print(
    #         f"({i}," +
    #         f"\t{sine_data[i]:5},\t{square_data[i]:5},\t{triangle_data[i]:5}," +
    #         f"\t{sawtooth_up_data[i]:5},\t{sawtooth_down_data[i]:5})")

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

    # ----------------- display
    display = feathereminDisplay9341.FeathereminDisplay9341()
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
    encoder = rotaryio.IncrementalEncoder(ss)
    print("Rotary encoder init OK")


    # pixel = neopixel.NeoPixel(ss, 6, 1)
    # pixel.brightness = 1.0

    print("\ninit_hardware OK!\n")
    return L0X, L4CD, apds, display, amp, encoder


# Map the distance in millimeters to a sample rate in Hz
#
def rangeToNote(mm: int) -> float:

    sr = ONE_OCTAVE[mm // 50] * (8000 // 440)
    return sr


# in: x
# returns: y
# sets: z
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
        # display.setTextArea3(f"Chromatic: {chromatic}")
        # pDisplay.setTextAreaL("Chromatic")

    else:
        return None

    return pWaveIndex, pChromatic


# --------------------------------------------------
# ------------------- begin main -------------------
def main():
    global wave_tables
    print("\nHello, fetheremin!")

    tof_L0X, tof_L4CD, gesture, display, amp, wheel = init_hardware()

    wave_tables = makeWaveTables()

    dac = audiopwmio.PWMAudioOut(AUDIO_OUT_PIN)

    dSleep = 0

    iter = 1
    sampleRateLast = -1

    wheelPositionLast = None

    waveIndex = 0
    waveName  = wave_tables[waveIndex][0]
    waveTable = wave_tables[waveIndex][1]

    print(f"Wave #{waveIndex}: {waveName}")
    display.setTextArea1(f"Waveform: {waveName}")
    display.setTextArea2(f"Sleep: {dSleep:.2f}")
    display.setTextArea3("")

    chromatic = False
    display.setTextAreaL(f"{'Chromatic' if chromatic else 'Continuous'}")
    display.setTextAreaR("L/R: wave\nU/D: Chrom")


    # Main loop
    while True:

        # Rotary encoder wheel?
        # negate the position to make clockwise rotation positive
        position = -wheel.position
        if position != wheelPositionLast:
            wheelPositionLast = position
            print(f"Wheel: {position}")

        # Gesture sensor?
        lastWaveIndex, lastChromatic = waveIndex, chromatic
        waveIndex, chromatic = handleGesture(gesture, waveIndex, chromatic)
        if waveIndex != lastWaveIndex:
            waveName  = wave_tables[waveIndex][0]
            waveTable = wave_tables[waveIndex][1]
            print(f"Wave #{waveIndex}: {waveName}")
            display.setTextArea1(f"Waveform: {waveName}")
        if chromatic != lastChromatic:
            display.setTextArea3(f"Chromatic: SHUTTHEFUCKUP")


        # Get the two ranges, as available. 
        # (TODO: Why is one always available, but the other is not?)
        #
        r1 = tof_L0X.range
        r2 = 0
        if tof_L4CD and tof_L4CD.data_ready:
            r2 = max(0, tof_L4CD.distance - 10)
            if r2 > 50:
                r2 = 0
            # print(f"r2 = {r2}")

            if r2 != 0:
                dSleep = r2/100
                display.setTextArea2(f"Sleep: {dSleep:.2f}")
                print(f"Sleep: {dSleep:.2f}")

            # must do this to get another reading
            tof_L4CD.clear_interrupt()

        if r1 > 0 and r1 < 500:

            # TODO: do we really need to sleep after starting a sample, 
            # or should we just keep going till the paramters change?
            
            if chromatic:
                sampleRate = int(rangeToNote(r1))
                if sampleRate != sampleRateLast:

                    sampleRateLast = sampleRate
                    print(f"Chrom: {waveName} #{iter}: {r1} mm -> {sampleRate} Hz; sleep {dSleep:.2f} ")
                    waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)
                    dac.play(waveSample, loop=True)
                    time.sleep(dSleep)

            else: # "continuous", not chromatic; more "theremin-like"?
                
                sampleRate = int(30*r1 + 1000)
                print(f"Cont: {waveName} #{iter}: {r1} mm -> {sampleRate} Hz; sleep {dSleep:.2f} ")
                waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)
                dac.play(waveSample, loop=True)
                time.sleep(dSleep)

        else: # no proximity detected
            dac.stop()

        iter += 1


main() # :-)
