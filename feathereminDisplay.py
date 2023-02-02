# SPDX-FileCopyrightText: 2023 dr cran's 3-D house of tofu
#
# SPDX-License-Identifier: Unlicense
"""
Original Author: Mark Roberts (mdroberts1243) from Adafruit code
"""

import board
import displayio
import terminalio

# original comment (what does it mean?):
#   can try import bitmap_label below for alternative
from adafruit_display_text import label
from adafruit_display_text.scrolling_label import ScrollingLabel
import adafruit_displayio_sh1107


class FeathereminDisplay:

    # SH1107 is vertically oriented 64x128
    WIDTH  = 128
    HEIGHT =  64
    BORDER =   2

    LINE_HEIGHT = 12

    splash_ = None
    text_area_1_ = None
    text_area_2_ = None
    text_area_3_ = None

    def __init__(self) -> None:

        displayio.release_displays()
        # oled_reset = board.D9

        i2c = board.I2C()  # on the Feather 2040, this is both SCA/SCL and STEMMA
        display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

        display = adafruit_displayio_sh1107.SH1107(
            display_bus, width=self.WIDTH, height=self.HEIGHT, rotation=0
        )

        # Make the display context
        self.splash_ = displayio.Group()
        display.show(self.splash_)

        self.text_area_1_ = label.Label(terminalio.FONT, text="", 
                        scale=1, color=0xFFFFFF, x=self.BORDER, y=self.LINE_HEIGHT)
        self.splash_.append(self.text_area_1_)

        self.text_area_2_ = label.Label(terminalio.FONT, text="", 
                        scale=1, color=0xFFFFFF, x=self.BORDER, y=2*self.LINE_HEIGHT)
        self.splash_.append(self.text_area_2_)
        
        self.text_area_3_ = label.Label(terminalio.FONT, text="", 
                        scale=1, color=0xFFFFFF, x=self.BORDER, y=3*self.LINE_HEIGHT)
        self.splash_.append(self.text_area_3_)
        


        ## for this to work we need to expose an update() method?
        #
        # text = "Hello world CircuitPython scrolling label"
        # my_scrolling_label = ScrollingLabel(
        #     terminalio.FONT, text=text, max_characters=20, animate_time=0.3
        # )
        # my_scrolling_label.x = 10
        # my_scrolling_label.y = 10
        # self.splash_.append(my_scrolling_label)

    # end __init__

    def setTextArea1(self, pText):
        self.text_area_1_.text = pText

    def setTextArea2(self, pText):
        self.text_area_2_.text = pText

    def setTextArea3(self, pText):
        self.text_area_3_.text = pText
