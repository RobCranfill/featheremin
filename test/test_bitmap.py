# SPDX-FileCopyrightText: 2019 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import board
import displayio
import terminalio
import adafruit_imageload
from adafruit_display_text import label

#  cran display = board.DISPLAY

import adafruit_ili9341

# Release any resources currently in use for the displays
displayio.release_displays()

spi = board.SPI()

tft_cs = board.A2
tft_dc = board.A0
tft_reset = board.A1

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset
)
display = adafruit_ili9341.ILI9341(display_bus, rotation=180, width=320, height=240)


# Make the display context

bitmap, palette = adafruit_imageload.load("/background.bmp",
                                          bitmap=displayio.Bitmap,
                                          palette=displayio.Palette)

# Create a TileGrid to hold the bitmap
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

# Create a Group to hold the TileGrid
group = displayio.Group()

# Add the TileGrid to the Group
group.append(tile_grid)

# Add the Group to the Display
display.show(group)



# add?

# # Draw a green background
# color_bitmap = displayio.Bitmap(320, 240, 1)
# color_palette = displayio.Palette(1)
# color_palette[0] = 0x00FF00  # Bright Green

# bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

# group.append(bg_sprite)

# # Draw a smaller inner rectangle
# inner_bitmap = displayio.Bitmap(280, 200, 1)
# inner_palette = displayio.Palette(1)
# inner_palette[0] = 0xAA0088  # Purple
# inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=20, y=20)
# group.append(inner_sprite)

# Draw a label
text_group = displayio.Group(scale=3, x=57, y=120)
text = "Hello, Cran!"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00)
text_group.append(text_area)  # Subgroup for text scaling
group.append(text_group)

# end add


# Loop forever so you can enjoy your image
while True:
    pass


