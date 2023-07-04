# being an un-committed file that I can point to whatever I want to run next....

# ----------------------------------------------------
# import supervisor
# supervisor.runtime.autoreload = False  # CirPy 8 and above
# #supervisor.disable_autoreload()  # CirPy 7 and below

# ----------------------------------------------------
# This runs my main project code:
# import feathereminMain
# while True:
#     pass


# Other test code, found in ./test directory.
# ----------------------------------------------------
# ----------------------------------------------------
# This lets us run stuff in the 'test' subdirectory:
import sys
sys.path.insert(0, 'test')

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


print("Fell off end of main! No test to run?")
while True:
    pass
