# This 'main' file just imports whatever code I really want to run.
# That is, the main project file or maybe test code.

# ----------------------------------------------------
import supervisor
supervisor.runtime.autoreload = False  # CirPy 8 and above

DO_MAIN_CODE = True

# ----------------------------------------------------
# This runs the main project code:
if DO_MAIN_CODE:
    import feathereminMain
    print("Featheremin run done.")
    while True:
        pass

# import WTF as wtf
# w = wtf.WTF()
# w.test()
# while True:
#     pass



# import board, feathereminDisplay2 as displayClass
# TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET = board.A2, board.A0, board.A1

# display = displayClass.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET, True)

# print(f"feathereminDisplay2 init OK? {display.init_OK}")

# if display.init_OK:
#     display.test() # does not return
# else:
#     print("blork! init failed!")
#     while True:
#         pass


# Other test code, found in ./test directory.
# ----------------------------------------------------
# ----------------------------------------------------
# This lets us run stuff in the 'test' subdirectory:
import sys
sys.path.insert(0, 'test')
# sys.path.insert(len(sys.path), 'test')
# sys.path.insert(len(sys.path), '..')

# SOUND TESTS
# doesn't work in /test dir
# import fallingForever

# import fallingForeverObj as ffo
# ff = ffo.FallingForever()
# ff.test()

# import derpNote
# import eightiesArp

# MISC TESTS OF MINE
#
# import test_display2

# import test_feathereminSynth
# import test_2_L0X_testbed

# import test_VL53L0X
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
