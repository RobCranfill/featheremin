import array
import audiocore
import audiopwmio
import board
import busio
import math
import time

import adafruit_vl53l0x
import adafruit_apds9960.apds9960

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

# # test
#     # check for gesture
# while True:
#     g = gesture.gesture()
#     while g == 0:
#         g = gesture.gesture()
#     print(f"Saw gesture: {g}")

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
while True:
    r = tof.range
    if (r < 500):

        # map r(0-500) to f(1000-10000) ?

        # sampleRate = int((r / 50) * 1000)
        sampleRate = int(30*(500-r) + 1000)
        print(f"#{iter}: {r} mm -> {sampleRate}")
        sine_wave = audiocore.RawSample(sine_wave_data, sample_rate=sampleRate)
        dac.play(sine_wave, loop=True)
        time.sleep(bleepTime)
        dac.stop()
    else:
        time.sleep(sleepTime)
    iter += 1

    # check for gesture
    g = gesture.gesture()
    if g != 0:
        print(f"Saw gesture: {g}")
        if g == 1:
            bleepTime -= 0.05
        if g == 2:
            bleepTime += 0.05

print("Done!")


