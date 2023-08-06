# This 'main' file just imports whatever code I really want to run.
# That is, the main project file or maybe test code.

# ----------------------------------------------------
import supervisor
supervisor.runtime.autoreload = False  # CirPy 8 and above

# # ----------------------------------------------------
# # This runs the main project code:
import feathereminMain
print("Feateremin test done.")
while True:
    pass


# Other test code, found in ./test directory.
# ----------------------------------------------------
# ----------------------------------------------------
# This lets us run stuff in the 'test' subdirectory:
import sys
sys.path.insert(0, 'test')

# import test_display2
import test_feathereminSynth
# import test_2_L0X_testbed

# import test_feathereminDisp
# import test_bitmap
# import test_range_and_sound
# import test_2_L0Xs # currently fails, due to HW issue
# import test_drone_synthio_I2S
# import test_TFT22 # basic display test
# import test_max98357a
# import test_wheel
# import test_neopixel

# no longer around or useful?
# ----------------------------------------------------
# # audio test stuff
# import i2s_test2
# import synthio_rude_noises_cran
# import synthio_tiny_lfo_song_2
# import synthio_tiny_lfo_song
# import simpleRangeSynth

## dumb banner code - not working!
# import banner
# b = banner.Banner()
# b.test("You are a ....")
# print("Fuk")
# while True:
#     pass


print("Fell off end of main! No test to run?")
while True:
    pass
