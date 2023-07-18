# ----------------------------------------------------
# test featheremin display object

# test v1 or v2?
TEST_OLD_CODE = False

import board
if TEST_OLD_CODE:
    import feathereminDisplay1 as featherDisplay
else:
    import feathereminDisplay2 as featherDisplay

TFT_DISPLAY_CS = board.A2
TFT_DISPLAY_DC = board.A0
TFT_DISPLAY_RESET = board.A1

if TEST_OLD_CODE:
    display = featherDisplay.FeathereminDisplay(180, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)
else:
    # FIXME: bitmap is problematic! 
    use_bitmap = True
    display = featherDisplay.FeathereminDisplay(180, use_bitmap, TFT_DISPLAY_CS, TFT_DISPLAY_DC, TFT_DISPLAY_RESET)

print("Display init OK?")

display.test() # does not return
