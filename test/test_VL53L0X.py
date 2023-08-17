# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of the VL53L0X distance sensor.
# Will print the sensed range/distance every second.
import board
import busio
import neopixel
import time

import adafruit_vl53l0x

import cran_vlx


USE_ALT_ADDR = True
L0X_B_ALTERNATE_I2C_ADDR = 0x30

def dual_test():
    cvlx = cran_vlx.CranVLX()
    tof_a, tof_b = cvlx.getSensors()
    while True:
        print(f"A: {tof_a.range}, B: {tof_b.range}")
        time.sleep(0.1)


def single_test():

    # Initialize I2C bus and sensor.
    # i2c = busio.I2C(board.SCL, board.SDA)
    i2c = board.STEMMA_I2C()
    if USE_ALT_ADDR:
        vl53 = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
    else:
        vl53 = adafruit_vl53l0x.VL53L0X(i2c)

    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)


    # Optionally adjust the measurement timing budget to change speed and accuracy.
    # See the example here for more details:
    #   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
    # For example a higher speed but less accurate timing budget of 20ms:
    # vl53.measurement_timing_budget = 20000
    # Or a slower but more accurate timing budget of 200ms:
    # vl53.measurement_timing_budget = 200000
    # The default timing budget is 33ms, a good compromise of speed and accuracy.

    # Main loop will read the range and print it every second.
    while True:
        r = vl53.range
        print(f"Range: {r}mm")
        pixel.fill((r, 0, 0))
        time.sleep(.1)


def continuous_test():

    # SPDX-FileCopyrightText: 2021 Smankusors for Adafruit Industries
    # SPDX-License-Identifier: MIT

    # Simple demo of the VL53L0X distance sensor with continuous mode.
    # Will print the sensed range/distance as fast as possible.

    print("CONTINUOUS TEST")

    # Initialize I2C bus and sensor.
    i2c = busio.I2C(board.SCL, board.SDA)
    vl53 = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)

    # cran - why no start_continuous?
    print(f"vl53.is_continuous_mode: {vl53.is_continuous_mode}")
    vl53.continuous_mode()

    vl53.start_continuous()
    print(f"vl53.is_continuous_mode: {vl53.is_continuous_mode}")

    # Optionally adjust the measurement timing budget to change speed and accuracy.
    # See the example here for more details:
    #   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
    # For example a higher speed but less accurate timing budget of 20ms:
    # vl53.measurement_timing_budget = 20000
    # Or a slower but more accurate timing budget of 200ms:
    vl53.measurement_timing_budget = 200000
    # The default timing budget is 33ms, a good compromise of speed and accuracy.

    # You will see the benefit of continous mode if you set the measurement timing
    # budget very high, while your program doing something else. When your program done
    # with something else, and the sensor already calculated the distance, the result
    # will return instantly, instead of waiting the sensor measuring first.

    # Main loop will read the range and print it every second.
    with vl53.continuous_mode():
        while True:
            # try to adjust the sleep time (simulating program doing something else)
            # and see how fast the sensor returns the range
            time.sleep(1)

            curTime = time.time()
            print("Range: {0}mm ({1:.2f}ms)".format(vl53.range, time.time() - curTime))


def single_mode_test():

    i2c = board.STEMMA_I2C()
    if USE_ALT_ADDR:
        vl53 = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
    else:
        vl53 = adafruit_vl53l0x.VL53L0X(i2c)

    print(f"vl53.is_continuous_mode: {vl53.is_continuous_mode}")
    print(f"vl53.measurement_timing_budget: {vl53.measurement_timing_budget}")
    while True:
        if vl53.data_ready:
            print(f"Range: {vl53.range}mm")
            # time.sleep(.1)
        else:
            print("Not ready")
            time.sleep(1)

print("test_VL53L0X....\n\n")
# single_test()
# dual_test()

continuous_test()
# single_mode_test()