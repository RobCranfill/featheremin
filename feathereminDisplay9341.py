# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Display object for
    Adafruit 2.2" TFT Display - 2.2" 18-bit color TFT LCD display
    AdafruitProduct ID: 1480
and using the Adafruit CircuitPython DisplayIO ILI9341 or compatible module.

Pinouts are for the 2.4" TFT FeatherWing or Breakout with a Feather M4 or M0.
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

L0X_RESET_OUT = board.D4

class FeathereminDisplay9341:

    def __init__(self) -> None:

        splash_ = None
        text_area_1_ = None
        text_area_2_ = None
        text_area_3_ = None

        # Release any resources currently in use for the displays
        displayio.release_displays()

        spi = board.SPI()
        tft_cs = board.A2
        tft_dc = board.A0

        display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.A1)
        try:
            display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240, rotation=180)
        except:
            print("No display found?")
            sys.exit(1) # FIXME: this is probably rude

        # Make the display context
        splash = displayio.Group()
        display.show(splash)

        # Draw a green background
        color_bitmap = displayio.Bitmap(320, 240, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x00FF00  # Green

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

        splash.append(bg_sprite)

        # Draw a smaller inner rectangle
        inner_bitmap = displayio.Bitmap(280, 200, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0xAA0088  # Purple
        inner_palette[0] = 0x0000FF  # no, blue!
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=20, y=20)
        splash.append(inner_sprite)


        # Draw a label
        text_group = displayio.Group(scale=2, x=40, y=40)

        self.text_area_1_ = label.Label(terminalio.FONT, text="text_area_1_", color=0xFFFF00)
        text_group.append(self.text_area_1_)  # Subgroup for text scaling

        self.text_area_2_ = label.Label(terminalio.FONT, text="text_area_2_", color=0xFFFF00, y=10)
        text_group.append(self.text_area_2_)  # Subgroup for text scaling

        self.text_area_3_ = label.Label(terminalio.FONT, text="text_area_3_", color=0xFFFF00, y=20)
        text_group.append(self.text_area_3_)  # Subgroup for text scaling


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
