"""Make noises, based on a time-of-flight sensor.
    With hardware reset.
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

# https://learn.adafruit.com/adafruit-apds9960-breakout/circuitpython
from adafruit_apds9960.apds9960 import APDS9960

# https://docs.circuitpython.org/projects/seesaw/en/latest/
from adafruit_seesaw import seesaw, rotaryio, digitalio


VL53L0X_RESET_OUT = board.A0
AUDIO_OUT_PIN = board.A1

ONE_OCTAVE = [440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 83.99, 830.61]

print("hello fetheremin!")

# Generate one period of various waveforms.
# Should there be an odd or even number of samples? we want to start and end with zeros, or at least some number.
#
length = 8000 // 440 + 1

sine_wave_data = array.array("H", [0] * length)
square_wave_data = array.array("H", [0] * length)
triangle_wave_data = array.array("H", [0] * length)
sawtooth_up_wave_data = array.array("H", [0] * length)
sawtooth_down_wave_data = array.array("H", [0] * length)

waves = [
    ("sine", sine_wave_data), 
    ("square", square_wave_data), 
    ("triangle", triangle_wave_data),
    ("saw up", sawtooth_up_wave_data),
    ("saw down", sawtooth_down_wave_data)]


for i in range(length):
    sine_wave_data[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
    if i < length/2:
        square_wave_data[i] = 0
        triangle_wave_data[i] = 2 * int(2**16 * i/length)
    else:
        square_wave_data[i] = int(2 ** 16)-1
        triangle_wave_data[i] = triangle_wave_data[length-i-1]
    sawtooth_up_wave_data[i] = int(i*2**16/length)
    sawtooth_down_wave_data[i] = 2**16 - sawtooth_up_wave_data[i] - 1

print(f"Wave tables: {length} entries")
print(f"{[w[0] for w in waves]}")
for i in range(length):
    print(f"({i},\t{sine_wave_data[i]},\t{square_wave_data[i]},\t{triangle_wave_data[i]},\t{sawtooth_up_wave_data[i]},\t{sawtooth_down_wave_data[i]})")


def init_hardware():
    """Initialize various hardware items.
    Namely, the I2C bus, Time of Flight sensor, gesture sensor, rotary encoder, OLED display.

    None of this checks for errors (missing hardware) yet - it will just malf.

    Returns:
        list of objects: the various harware items initialized.
    """

    # Easist way to init I2C on a Feather:
    i2c = board.STEMMA_I2C()

    # For fun
    i2c.try_lock()
    print(f"I2C scan: {[hex(x) for x in i2c.scan()]}")
    i2c.unlock()

    # ----------------- VL53L0X time-of-flight sensor 
    # reset the ToF sensor - take its XSHUT pin low, then high
    print("Resetting VL53L0X...")
    xshut = feather_digitalio.DigitalInOut(VL53L0X_RESET_OUT)
    xshut.direction = feather_digitalio.Direction.OUTPUT
    xshut.value = 0
    time.sleep(0.1) # needed?
    xshut.value = 1

    tof = adafruit_vl53l0x.VL53L0X(i2c)
    print("ToF init OK")


    # ----------------- APDS9960 gesture/proximity/color sensor 
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    apds.enable_gesture = True
    apds.rotation = 180


    # ----------------- Rotary encoder
    ss = seesaw.Seesaw(i2c, addr=0x36)
    rotEnc = rotaryio.IncrementalEncoder(ss)

    # why bother with all this?
    # seesaw_product = (ss.get_version() >> 16) & 0xFFFF
    # print(f"Found Seesaw product {seesaw_product}")
    # if seesaw_product != 4991:
    #     print("Wrong firmware loaded? Expected 4991")


    # ----------------- OLED display
    oledDisp = feathereminDisplay.FeathereminDisplay()

    return tof, apds, rotEnc, oledDisp


# map distance in millimeters to a sample rate in Hz
# mm in range (0,500)
#
def rangeToRate(mm: int) -> float:

    # simple, no chunking:
    if False:
        sr = int(30*mm + 1000)

    # 10 chunks - ok
    if False:
        sr = mm // 50  # sr = {0..10}
        sr = sr * 1000 # sr = {0K..10K}

    sr = ONE_OCTAVE[mm // 50] * (8000 // 440)
    
    return sr


tof, gesture, wheel, display = init_hardware()
 
dac = audiopwmio.PWMAudioOut(AUDIO_OUT_PIN)

sleepTime = 0.2
bleepTime = 0.2

nTries = 100
iter = 1
sampleRateLast = -1

useSineWave = True
wheelPositionLast = None
chunkMode = False
chunkSleep = 0.1

waveIndex = 0
waveName  = waves[waveIndex][0]
waveTable = waves[waveIndex][1]

print(f"Wave #{waveIndex}: {waveName}")
display.setTextArea1(f"Waveform: {waveName}")

while True:

    wheelPosition = wheel.position
    if wheelPosition != wheelPositionLast:
        wheelPositionLast = wheelPosition
        print(f"Position: {wheelPosition}")
        chunkSleep = 0.1 + wheelPosition/100
        if chunkSleep < 0:
            chunkSleep = 0

    g = gesture.gesture()
    if g == 1:
        waveIndex += 1
        if waveIndex >= len(waves):
            waveIndex = 0
        waveName  = waves[waveIndex][0]
        waveTable = waves[waveIndex][1]
        print(f"Wave #{waveIndex}: {waves[waveIndex][0]}")
        display.setTextArea1(f"Waveform: {waveName}")

    elif g == 2:
        waveIndex -= 1
        if waveIndex < 0:
            waveIndex = len(waves) - 1
        waveName  = waves[waveIndex][0]
        waveTable = waves[waveIndex][1]
        print(f"Wave #{waveIndex}: {waves[waveIndex][0]}")
        display.setTextArea1(f"Waveform: {waveName}")

    elif g == 3:
        print("left")
    elif g == 4:
        print("right")

    r = tof.range
    if r > 0 and r < 500:

        if chunkMode:
            sampleRate = int(rangeToRate(r))
            if sampleRate != sampleRateLast:

                dac.stop()

                # sampleRate = int(30*(500-r) + 1000)
                # sampleRate = int(30*r + 1000)

                print(f"#{iter}: {r} mm -> {sampleRate} Hz {'sine' if useSineWave else 'square'}")

                waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)

                sampleRateLast = sampleRate
                dac.play(waveSample, loop=True)
                time.sleep(0.1)
            # time.sleep(bleepTime)
            # dac.stop()

        else: # "continuous", not chunkMode
            
            # sampleRate = int(rangeToRate(r))
            sampleRate = int(30*r + 1000)

            # dac.stop()

            print(f"Cont: {waveName} #{iter}: {r} mm -> {sampleRate} Hz {chunkSleep} ")

            waveSample = audiocore.RawSample(waveTable, sample_rate=sampleRate)
            
            dac.play(waveSample, loop=True)

            time.sleep(chunkSleep)

            # time.sleep(bleepTime)
            # dac.stop()
            
    else:
        dac.stop()
        # pass
        # time.sleep(sleepTime)
        
    iter += 1
    # print("Done!")
