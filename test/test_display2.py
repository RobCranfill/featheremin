# ----------------------------------------------------
# test featheremin display object

import board
import feathereminDisplay2

TFT_DISPLAY_CS = board.A2
TFT_DISPLAY_DC = board.A0
TFT_DISPLAY_RESET = board.A1

display = feathereminDisplay2.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)
print("feathereminDisplay2 init OK?")
display.test() # does not return
