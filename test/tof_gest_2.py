"""Make noises, using a time-of-flight sensor and a 'gesture' sensor.

Uses a VL53L0X time-of-flight sensor and a APDS-9960 sensor, both from Adafruit,
to determine sound parameters.

Version 2: can I get rid of the pauses?
"""

import array
import audiocore
import audiopwmio
import board
import busio
import math
import time

import adafruit_vl53l0x
import adafruit_apds9960.apds9960

# TODO: put this in __init ??? no, cuz then i'd have to use globals for the sensors?
def init_hardware():
    
    # Initialize I2C bus and sensor for the Time of Flight sensor
    USE_STEMMA = False
    if USE_STEMMA:
        tof_i2c = board.STEMMA_I2C()
    else:
        tof_i2c = busio.I2C(board.D9, board.D6)
    tof = adafruit_vl53l0x.VL53L0X(tof_i2c)

    prox_i2c = board.STEMMA_I2C()
    gesture = adafruit_apds9960.apds9960.APDS9960(prox_i2c)
    gesture.enable_gesture = True
    gesture.enable_proximity = True # this is needed too!

    return (tof, gesture)


"""
Loop forever, emittimng bleeps
"""
def go():

    tof, gesture = init_hardware()

    # Generate one period of a sine wave
    length = 8000 // 440
    sine_wave_data = array.array("H", [0] * length)
    for i in range(length):
        sine_wave_data[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)

    dac = audiopwmio.PWMAudioOut(board.A0)

    sleepTime = 0.2
    bleepTime = 0.2

    nTries = 100
    sampleRate = 1000
    iter = 1
    rLast = -1
    while True:
        r = tof.range
        if (r < 500):

            # map r(500-0) to f(1000-11000) ?

            if r != rLast:
                sampleRate = int(30*(500-r) + 1000)
                print(f"#{iter}: {r} mm -> {sampleRate} Hz")
                dac.stop()
                sine_wave = audiocore.RawSample(sine_wave_data, sample_rate=sampleRate)
                rLast = r
                dac.play(sine_wave, loop=True)

            # time.sleep(bleepTime)
            # dac.stop()

        else:
            dac.stop()
            # pass
            # time.sleep(sleepTime)
            
        iter += 1

        # check for gesture
        g = gesture.gesture()
        if g != 0:
            # print(f"Saw gesture: {g}")
            if g == 1: # up
                print(f"up!")
                bleepTime -= 0.05
                if bleepTime <= 0:
                    bleepTime = 0
            elif g == 2: # down
                print(f"down!")
                bleepTime += 0.05
                dac.stop()
            elif g == 3: # right-to-left
                print(f"left!")
                sleepTime += 0.1
            elif g == 4: # left-to-right
                print(f"right!")
                sleepTime -= 0.1
                if sleepTime <= 0:
                    sleepTime = 0
            print(f"  -> Delay {bleepTime}, sleep {sleepTime}")


        # # useful? - no, you can't do prox and gestures at the same time!
        # p = gesture.proximity
        # if p > 0:
        #     print(f"  p = {p}")

    print("Done!")

