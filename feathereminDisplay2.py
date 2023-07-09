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
import random
import time
import sys
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import adafruit_ili9341
import adafruit_imageload
from digitalio import DigitalInOut, Direction
from adafruit_vl53l0x import VL53L0X

MESSAGE_TEXT_COLOR = 0xFF0000
STATUS_TEXT_COLOR = 0X000000

FONT_TO_LOAD = "SFDigitalReadout-Medium-24.bdf"

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


        font = None
        fontScale = 2
        try:
            font = bitmap_font.load_font("/" + FONT_TO_LOAD)
            fontScale = 1
        except:
            print("Can't load custom font!")
            font = terminalio.FONT


        # Labels
        # Because this is scaled by 2, the coordinates are half what you'd expect.
        # (The display area is effectively 160 x 120)
        #
        text_group = displayio.Group(scale=fontScale, x=0, y=72)

        self.text_area_1_ = label.Label(font, text="", color=MESSAGE_TEXT_COLOR, x=20, y=4)
        text_group.append(self.text_area_1_)  # Subgroup for text scaling

        self.text_area_2_ = label.Label(font, text="", color=MESSAGE_TEXT_COLOR, x=20, y=50)
        text_group.append(self.text_area_2_)

        self.text_area_3_ = label.Label(font, text="", color=MESSAGE_TEXT_COLOR, x=20, y=100)
        text_group.append(self.text_area_3_)

        self.text_area_l_ = label.Label(font, text="", color=STATUS_TEXT_COLOR, x=6, y=666)
        text_group.append(self.text_area_l_)

        self.text_area_r_ = label.Label(font, text="", color=STATUS_TEXT_COLOR, x=66, y=666)
        text_group.append(self.text_area_r_)

        background_group.append(text_group)

        # Load the sprite sheet bitmap
        sprite_sheet, led_palette = adafruit_imageload.load("/led_sprite_sheet.bmp",
                                                        bitmap=displayio.Bitmap,
                                                        palette=displayio.Palette)
        
        # The color we want to be transparent seems to be the last one in the palette.
        # Is this always true?
        led_palette.make_transparent(len(led_palette)-1)

        # Create a sprite (tilegrid)
        self.led_sprite = displayio.TileGrid(sprite_sheet, pixel_shader=led_palette,
                                    width = 1, height = 1,
                                    tile_width = 16, tile_height = 16)

        # Create a Group to hold the sprite
        led_group = displayio.Group(scale=1)
        led_group.append(self.led_sprite)

        # Set sprite location
        led_group.x =  25
        led_group.y = 203

        background_group.append(led_group)

    # end __init__

    # Make the LED red? the lit, red led is first in the sprite sheet, so index 0
    def setLEDStatus(self, status: bool):
        self.led_sprite[0] = 0 if status else 1
 
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

        self.setTextArea2("You are a")
        self.setTextArea3("hideous orangutan!")
        self.setTextAreaL("")
        self.setTextAreaR("Testing")

        i = 0
        while True:
            self.setLEDStatus(random.choice([True, False]))
            self.setTextArea1(f"Tick {i}...")
            i += 1
            time.sleep(.5)

        print("Display test waiting, so display doesn't get erased.")

        while True:
            pass