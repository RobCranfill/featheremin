# test/demo new gesture control
import board
from adafruit_apds9960.apds9960 import APDS9960
import feathereminDisplay3 as featherDisplay
import gestureMenu

# new display class allowing arbitrary number of text areas
display = featherDisplay.FeathereminDisplay(
    180, boardPinCS=board.A2, boardPinDC=board.A0, boardPinReset=board.A1, nTextAreas=4)


# Data for the menu.
#
# FIXME: The first option for each item will be the one intially selected.
# 
menu = [ # 'item', 'options', *index* of default
    ["Item 1",   ["I1 opt 1", "I1 opt 2"], 0],
    ["Item 2",   ["I2 opt 1", "I2 opt 2", "I2 opt 3"], 0],
    ["Item 3",   ["I3 opt 1", "I3 opt 2", "I3 opt 3", "I2 opt 4"], 0],
    ["Item 4",   ["I4 opt 1", "I4 opt 2", "I4 opt 3"], 0],
    ["Item 5",   ["I5 opt 1", "I5 opt 2"], 0],
    ]


i2c = None
try:
    i2c = board.STEMMA_I2C()
except:
    print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")

# ----------------- APDS9960 gesture/proximity/color sensor
apds = None
try:
    apds = APDS9960(i2c)
except:
    print("Can't init APDS9960?")

gm = gestureMenu.GestureMenu(apds, display, menu, windowSize=4)

i = 0 # this shows that we can keep processing after looking for selections
while True:
    i += 1
    item, option = gm.getItemAndOption()
    if item is not None:
        print(f"Got a gesture @ {i}; Do something with {item} / {option}")
