"""
    Display object for
        Adafruit 2.2" TFT Display - 2.2" 18-bit color TFT LCD display
        AdafruitProduct ID: 1480
    and using the Adafruit CircuitPython DisplayIO ILI9341 or compatible module.

    Wired via SPI ("four wire") interface.

    The GPIO pins to use are passed in on object creation.

    Version 3: for new gesture menu scheme

"""
import board
import terminalio
import displayio
from adafruit_display_text import label
import adafruit_ili9341

import time
import sys
from digitalio import DigitalInOut, Direction
from adafruit_vl53l0x import VL53L0X

# Implements the FeathereminDisplay class:
class FeathereminDisplay:

    def __init__(self, p_rotation, boardPinCS, boardPinDC, boardPinReset) -> None:

        self.text_area_1_ = None
        self.text_area_2_ = None
        self.text_area_3_ = None

        # Release any resources currently in use for the displays
        displayio.release_displays()

        spi = board.SPI()

        # tft_cs = board.A2
        # tft_dc = board.A0
        # tft_reset = board.A1

        tft_cs, tft_dc, tft_reset = boardPinCS, boardPinDC, boardPinReset

        try:
            display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset)
            display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240, rotation=p_rotation)
        except:
            print("No ILI9341 display found?")
            # FIXME: what to do if construction fails?
            return

        # Make the display context
        splash = displayio.Group()
        display.show(splash)

        # Main background
        color_bitmap = displayio.Bitmap(320, 240, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x0000FF  # blue

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

        splash.append(bg_sprite)

        # Left control display
        l_bitmap = displayio.Bitmap(140, 80, 1)
        l_palette = displayio.Palette(1)
        l_palette[0] = 0x00FF00  #green
        l_sprite = displayio.TileGrid(l_bitmap, pixel_shader=l_palette, x=10, y=140)
        splash.append(l_sprite)

        # Right control display
        r_bitmap = displayio.Bitmap(140, 80, 1)
        r_palette = displayio.Palette(1)
        r_palette[0] = 0x00FF00  #green
        r_sprite = displayio.TileGrid(r_bitmap, pixel_shader=r_palette, x=170, y=140)
        splash.append(r_sprite)

        # Labels
        text_group = displayio.Group(scale=2, x=0, y=40)

        activeColor = 0xFFFFFF
        inactiveColor = 0x808080

        self.text_area_1_ = label.Label(terminalio.FONT, text="text_area_1_", color=inactiveColor, x=5, y=0)
        text_group.append(self.text_area_1_)  # Subgroup for text scaling

        self.text_area_2_ = label.Label(terminalio.FONT, text="text_area_2_", color=activeColor, x=5, y=10)
        text_group.append(self.text_area_2_)  # Subgroup for text scaling

        self.text_area_3_ = label.Label(terminalio.FONT, text="text_area_3_", color=inactiveColor, x=5, y=20)
        text_group.append(self.text_area_3_)  # Subgroup for text scaling

        self.text_area_l_ = label.Label(terminalio.FONT, text="Control L", color=0x000000, x=10, y=60)
        text_group.append(self.text_area_l_)  # Subgroup for text scaling

        self.text_area_r_ = label.Label(terminalio.FONT, text="Control R", color=0x000000, x=90, y=60)
        text_group.append(self.text_area_r_)  # Subgroup for text scaling

        splash.append(text_group)

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
        self.setTextArea1(" You are")
        self.setTextArea2(" hideous")
        self.setTextArea3("orangutan!")
        print("Display test waiting, so display doesn't get erased.")
        while True:
            pass