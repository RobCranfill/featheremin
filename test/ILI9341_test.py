# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This test will initialize the display using displayio and draw a solid green
background, a smaller purple rectangle, and some yellow text. All drawing is done
using native displayio modules.

Pinouts are now for my Adafruit Feather RP2040 "Featheremin" project.
"""
import board
import terminalio
import displayio
from adafruit_display_text import label
import adafruit_ili9341
import digitalio

print("ILI9341 test for Featheremin.....")

# Release any resources currently in use for the displays
displayio.release_displays()

spi = board.SPI()
tft_cs = board.A2
tft_dc = board.A0

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.A1)
display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

# Make the display context
splash = displayio.Group()
display.show(splash)

# Draw a green background
color_bitmap = displayio.Bitmap(320, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x00FF00  # Bright Green

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(280, 200, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0xAA0088  # Purple
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=20, y=20)
splash.append(inner_sprite)

# Draw a label
text_group = displayio.Group(scale=3, x=57, y=120)
text = "Hello World!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00)
text_group.append(text_area)  # Subgroup for text scaling
splash.append(text_group)

# added backlight code
backlight = digitalio.DigitalInOut(board.A3)
backlight.switch_to_output()
backlight.value = True

print("Test done!")

# if the code stops, the display gets erased. Why?
# so do this to wait forever:
while True:
    pass

