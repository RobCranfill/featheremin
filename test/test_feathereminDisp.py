# ----------------------------------------------------
# test featheremin display object

import feathereminDisplay1, board

TFT_DISPLAY_CS = board.A2
TFT_DISPLAY_DC = board.A0
TFT_DISPLAY_RESET = board.A1

display = feathereminDisplay1.FeathereminDisplay9341(0, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)
print("Display init OK?")
display.test() # does not return
