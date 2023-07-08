"""
    Class to wrap the display hardware in standard methods.
        Adafruit 2.2" TFT Display - 2.2" 18-bit color TFT LCD display
        AdafruitProduct ID: 1480
    and using the Adafruit CircuitPython DisplayIO ILI9341 or compatible module.

    Uses the SPI ("four wire") interface.
    Version 2, using a BMP file for a background.

"""
import board
import terminalio
import displayio
import time
import sys
from adafruit_display_text import label
import adafruit_ili9341
import adafruit_imageload
from digitalio import DigitalInOut, Direction
from adafruit_vl53l0x import VL53L0X

MESSAGE_TEXT_COLOR = 0xFF0000
STATUS_TEXT_COLOR = 0X000000

'''
    The display object.
    The GPIO pins to use are passed in on object creation.
'''
class FeathereminDisplay:

    def __init__(self, p_rotation, boardPinCS, boardPinDC, boardPinReset) -> None:

        self.text_area_1_ = None
        self.text_area_2_ = None
        self.text_area_3_ = None
        self.text_area_l_ = None
        self.text_area_r_ = None

        try:
            displayio.release_displays()
            spi = board.SPI()
            display_bus = displayio.FourWire(spi, command=boardPinDC, chip_select=boardPinCS, reset=boardPinReset)
            display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240, rotation=p_rotation)
        except:
            print("No ILI9341 display found?")
            # FIXME: what to do if construction fails?
            return

        bitmap, palette = adafruit_imageload.load("/background.bmp",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)

        tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette) # Create a TileGrid to hold the bitmap
        background_group = displayio.Group() # Create a Group to hold the TileGrid
        background_group.append(tile_grid) # Add the TileGrid to the Group
        display.show(background_group) # Add the Group to the Display

        # Labels
        # Because this is scaled by 2, the coordinates are half what you'd expect.
        # (The display area is effectively 160 x 120)
        #
        text_group = displayio.Group(scale=2, x=0, y=40)

        self.text_area_1_ = label.Label(terminalio.FONT, text="text_area_1_", color=MESSAGE_TEXT_COLOR, x=12, y=0)
        text_group.append(self.text_area_1_)  # Subgroup for text scaling

        self.text_area_2_ = label.Label(terminalio.FONT, text="text_area_2_", color=MESSAGE_TEXT_COLOR, x=14, y=30)
        text_group.append(self.text_area_2_)

        self.text_area_3_ = label.Label(terminalio.FONT, text="text_area_3_", color=MESSAGE_TEXT_COLOR, x=16, y=60)
        text_group.append(self.text_area_3_)

        self.text_area_l_ = label.Label(terminalio.FONT, text="Control L", color=STATUS_TEXT_COLOR, x=10, y=80)
        text_group.append(self.text_area_l_)

        self.text_area_r_ = label.Label(terminalio.FONT, text="Control R", color=STATUS_TEXT_COLOR, x=90, y=80)
        text_group.append(self.text_area_r_)

        background_group.append(text_group)

    # end __init__

    # "setters" for the text areas
    #
    def setTextArea1(self, pText):
        self.text_area_1_.text = pText

    def setTextArea2(self, pText):
        self.text_area_2_.text = pText

    def setTextArea3(self, pText):
        self.text_area_3_.text = pText

    def setTextAreaL(self, pText):
        self.text_area_l_.text = pText

    def setTextAreaR(self, pText):
        self.text_area_r_.text = pText

    '''
    This does not return!
    '''
    def test(self) -> NoReturn:
        self.setTextArea1("You are")
        self.setTextArea2("A hideous")
        self.setTextArea3("orangutan!")

        i = 1
        while True:
            self.setTextArea1(f"Tick {i}...")
            i += 1
            time.sleep(1)
            
        print("Display test waiting, so display doesn't get erased.")

        while True:
            pass