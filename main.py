
"""Make noises, based on a time-of-flight sensor.
    With harware reset.
"""

import array
import audiocore
import audiopwmio
import board
import busio
import digitalio
import math
import time
import sys

import adafruit_vl53l0x


AUDIO_OUT_PIN = board.A1


print("hello fetheremin!")

# Generate one period of a sine wave and a square wave
length = 8000 // 440
sine_wave_data = array.array("H", [0] * length)
square_wave_data = array.array("H", [0] * length)
for i in range(length):
    sine_wave_data[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
    if i < length/2:
        square_wave_data[i] = 0
    else:
        square_wave_data[i] = int(2 ** 15)

# for i in range(1, 11):
#     print(f"sin({i}) = {sine_wave_data[i]}")
# print()
# for i in range(1, 11):
#     print(f"squ({i}) = {square_wave_data[i]}")


def init_hardware():
    
    # reset the ToF sensor
    print("Resetting ToF...")
    xshut = digitalio.DigitalInOut(board.A0)
    xshut.direction = digitalio.Direction.OUTPUT
    # take it low, then high
    xshut.value = 0
    time.sleep(0.1)
    xshut.value = 1
    print("Reset ToF OK!?")

    # Initialize I2C bus and sensor for the Time of Flight sensor
    USE_STEMMA = True
    if USE_STEMMA:
        tof_i2c = board.STEMMA_I2C()
    else:
        tof_i2c = busio.I2C(board.D9, board.D6)

    # This seems to f* up the sensor!
    #
    # print("- I2C scan -----------")
    # tof_i2c.try_lock()
    # print(f"{tof_i2c.scan()}")
    # print("----------------------")
    
    tof = adafruit_vl53l0x.VL53L0X(tof_i2c)
    print("ToF init OK")

    return tof

ONE_OCTAVE = [440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 83.99, 830.61]

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


tof = init_hardware()
 
dac = audiopwmio.PWMAudioOut(AUDIO_OUT_PIN)

sleepTime = 0.2
bleepTime = 0.2

nTries = 100
iter = 1
sampleRateLast = -1

useSineWave = True

chunkMode = False
chunkSleep = 0.1

while True:
    r = tof.range
    if (r < 500):

        if chunkMode:
            sampleRate = int(rangeToRate(r))
            if sampleRate != sampleRateLast:

                dac.stop()

                # sampleRate = int(30*(500-r) + 1000)
                # sampleRate = int(30*r + 1000)

                # for fun, switch sine/square every 100 iterations
                useSineWave = (((iter // 100) % 2) == 1)
                print(f"#{iter}: {r} mm -> {sampleRate} Hz {'sine' if useSineWave else 'square'}")

                if useSineWave:
                    wave = audiocore.RawSample(sine_wave_data, sample_rate=sampleRate)
                else:
                    wave = audiocore.RawSample(square_wave_data, sample_rate=sampleRate)
                
                sampleRateLast = sampleRate
                dac.play(wave, loop=True)
                time.sleep(0.1)
            # time.sleep(bleepTime)
            # dac.stop()

        else: # not chunkMode
            
            # sampleRate = int(rangeToRate(r))
            sampleRate = int(30*r + 1000)

            # dac.stop()

            # for fun, switch sine/square every 100 iterations
            useSineWave = (((iter // 100) % 2) == 1)
            print(f"chunk #{iter}: {r} mm -> {sampleRate} Hz {'sine' if useSineWave else 'square'}")

            if useSineWave:
                wave = audiocore.RawSample(sine_wave_data, sample_rate=sampleRate)
            else:
                wave = audiocore.RawSample(square_wave_data, sample_rate=sampleRate)
            
            dac.play(wave, loop=True)

            time.sleep(chunkSleep)

            # time.sleep(bleepTime)
            # dac.stop()
            
    else:
        dac.stop()
        # pass
        # time.sleep(sleepTime)
        
    iter += 1
    # print("Done!")

