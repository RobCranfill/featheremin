# ----------------------------------------------------
# test featheremin display object

import board
import feathereminDisplay2 as displayClass

TFT_DISPLAY_CS = board.A2
TFT_DISPLAY_DC = board.A0
TFT_DISPLAY_RESET = board.A1

display = displayClass.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET, True)

print(f"feathereminDisplay2 init OK? {display.init_OK}")

if display.init_OK:
    display.test() # does not return
else:
    print("NOT TESTING, SINCE INIT FAILED! Stopping....")
    while True:
        pass

