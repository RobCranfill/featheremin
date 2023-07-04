
import time
import board
# import adafruit_vl53l0x
import neopixel

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
print("\nBlink!")

rInc = 1
r = 0
while True:
    if r>256 or r<0:
        rInc = -rInc
    r += rInc
    # print(f"{r}")
    pixel.fill((r, 0, 0))
    time.sleep(0.001)


# # Initialize I2C bus and sensor.
# i2c = board.STEMMA_I2C()
# vl53 = adafruit_vl53l0x.VL53L0X(i2c)
# print("VL53L0X OK!")

# # Optionally adjust the measurement timing budget to change speed and accuracy.
# # See the example here for more details:
# #   https://github.com/pololu/vl53l0x-arduino/blob/master/examples/Single/Single.ino
# # For example a higher speed but less accurate timing budget of 20ms:
# # vl53.measurement_timing_budget = 20000
# # Or a slower but more accurate timing budget of 200ms:
# # vl53.measurement_timing_budget = 200000
# # The default timing budget is 33ms, a good compromise of speed and accuracy.

# rLast = -1
# while True:
#     r = 10 * int(vl53.range/10)
#     if r != rLast:
#         rLast = r
#         if r < 512 and r > 0:
#             print(f"({r}, {r/2})")
#             pixel.fill((256-r/4, 0, 0))
#             # time.sleep(0.01)
#         else:
#             pixel.fill((0,128,0))


