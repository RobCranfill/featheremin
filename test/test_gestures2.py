# new gesture control
import board
from adafruit_apds9960.apds9960 import APDS9960
import feathereminDisplay3 as featherDisplay
import GestureMenu as gestureMenu


# class MenuItem():
#     def __init__(self, itemStr, optionsList, optionIndex):
#         self._itemStr = itemStr
#         self._optionsList = optionsList
#         self._selectedOption = optionsList[optionIndex]
#         self._isActive = False

#     def selectNextOption(self):
#         i = (self._optionsList.index(self._selectedOption) + 1) % len(self._optionsList)
#         self._selectedOption = self._optionsList[i]

#     def selectPrevOption(self):
#         i = (self._optionsList.index(self._selectedOption) - 1) % len(self._optionsList)
#         self._selectedOption = self._optionsList[i]
# # end class MenuItem

# class MenuHandler():
#     '''
#         behind the menu system.
#         first, you can use this to draw the menu and items in it.
#         also, if a gesture is detected, this class will let you know what changed.
#     '''
#     def __init__(self, menuListData) -> None:

#         # dictionary that includes user selection
#         self._stateDict = {}
#         self._itemList = []
#         self._selectedItemKey = None
#         for mItem in menuListData:

#             itemName = mItem[0]
#             optionsList = mItem[1]
#             optionDefaultIndex = mItem[2]

#             self._stateDict[itemName] = MenuItem(itemName, optionsList, optionDefaultIndex)
#             self._itemList.append(itemName)

#             # set first item as active - FIXME use specified defaults
#             if self._selectedItemKey is None:
#                 self._selectedItemKey = itemName

#         print(f"Dictionary: {self._stateDict}\n")
#         print(f"Items: {self._itemList}")

#     def getItems(self):
#         '''
#         list of all top-level menu 'items' (the keys thereto), in defined order (as we want in the menu list)
#         '''
#         return self._itemList

#     # the current selected item
#     def getSelectedItem(self):
#         return self._selectedItemKey

#     # FIXME: why is this here? why isn't it needed? i'm so confused....
#     # def getSelectedOption(self):
#     #     self._stateDict[self._selectedItemKey]._selectedOption

#     # the current option for the given item
#     def getItemOption(self, keyStr):
#         if keyStr is None:
#             return "?"
#         return self._stateDict[keyStr]._selectedOption
    
#     # list of all
#     def getOptionsForItem(self, keyStr):
#         return self._stateDict[keyStr]._optionsList

#     # select next item, wrapping
#     def selectNextItem(self):
#         i = (self._itemList.index(self._selectedItemKey) + 1) % len(self._itemList)
#         self._selectedItemKey = self._itemList[i]

#     # select prev item, wrapping
#     def selectPrevItem(self):
#         i = (self._itemList.index(self._selectedItemKey) - 1) % len(self._itemList)
#         self._selectedItemKey = self._itemList[i]

#     # set selected option to the next one in the list, wrapping
#     def setNextOption(self):
#         mi = self._stateDict[self._selectedItemKey]
#         mi.selectNextOption()

#     # set selected option to the prev one in the list, wrapping
#     def setPrevOption(self):
#         mi = self._stateDict[self._selectedItemKey]
#         mi.selectPrevOption()

# # end class MenuHandler


# # we want:
# # if   gestureValue == 1: # down
# # elif gestureValue == 2: # up
# # elif gestureValue == 3: # right
# # elif gestureValue == 4: # left

# class GestureMenu:
#     def __init__(self, display, menuData, windowSize=4):

#         self._display = display
#         self._windowSize = windowSize

#         i2c = None
#         try:
#             i2c = board.STEMMA_I2C()
#         except:
#             print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")

#         # ----------------- APDS9960 gesture/proximity/color sensor
#         # self._apds = None
#         try:
#             self._apds = APDS9960(i2c)
#             self._apds.enable_proximity = True
#             self._apds.enable_gesture = True
#             self._apds.rotation = 0 # this is correct for my upside-down test setup at OS; was 90 (?!)
#             print("APDS9960 init OK")
#         except:
#             print("**** No APDS9960? Continuing....")
        
#         self._menuHandler = MenuHandler(menuData)
#         self.updateDisplay()

#     # end GestureMenu.__init__


#     def updateDisplay(self):
#         # with current state
#         # draw windowSize items centered (?) on the selected one.
#         # - only tested for odd values of _windowSize
#         # - FIXME actually, pretty much only works for _windowSize = 3
#         # 
#         allKeys = self._menuHandler.getItems()

#         # find the keys of the menu items to display
#         # build a list of the keys, twice
#         keyList = []
#         for k in allKeys:
#             keyList.append(k)
#         for k in allKeys:
#             keyList.append(k)
        
#         kLoc = keyList.index(self.getSelectedItem(), 1)
#         # print(f"kLoc {kLoc}")

#         displayKeys = keyList[kLoc-1:kLoc+2]
#         print(f"displayKeys {displayKeys}")

#         # TODO: the display object needs to have an iterable list of text areas

#         self._display.setTextArea1(f"{displayKeys[0]} = {self.getItemOption(displayKeys[0])}")
#         self._display.setTextArea2(f"{displayKeys[1]} = {self.getItemOption(displayKeys[1])}")
#         self._display.setTextArea3(f"{displayKeys[2]} = {self.getItemOption(displayKeys[2])}")


#     # the menu item whose value changed
#     def getSelectedItem(self):
#         return self._menuHandler.getSelectedItem()
    
#     # current option value for changed menu item
#     def getSelectedOption(self):
#         return self._menuHandler.getItemOption(self.getSelectedItem())
    
#     # current option value for given menu item
#     def getItemOption(self, itemStr):
#         return self._menuHandler.getItemOption(itemStr)

#     # get a gesture, if any; if so, update menu
#     # only return gestures that 
#     def getGesture(self):

#         g = self._apds.gesture()
#         if g == 0:
#             return None
        
#         if g == 1: # down
#             self._menuHandler.selectNextItem()
#         elif g == 2: # up
#             self._menuHandler.selectPrevItem()
#         elif g == 3: # right
#             self._menuHandler.setNextOption()
#         elif g == 4: # left
#             self._menuHandler.setPrevOption()

#         self.updateDisplay()

#         return g
#         # end getGesture

#     # end class GestureMenu


display = featherDisplay.FeathereminDisplay(
    180, boardPinCS=board.A2, boardPinDC=board.A0, boardPinReset=board.A1)


# Data for the menu.
#
# FIXME: The first option for each item will be the one intially selected.
# 
menu = [ # 'item', 'options', *index* of default
    ["Waveform",    ["Sine", "Square", "Saw"], 0],
    ["LFO",         ["Off", "Tremelo", "Vibrato", "Drone"], 0],
    ["Chromatic",   [True, False], 0],
    ["Bogus1",      ["A", "B", "C", "D"], 0],
    ["Util",        ["Restart", "Shutdown"], 0]
    # ["Volume",      [range(0, 101, 10)], 11], # 0 to 100% in 10% increments
    # ["Delay",       [range(10)], 0] # milliseconds
    ]

gm = GestureMenu(display, menu, windowSize=3)

i = 0
while True:
    i += 1
    g = gm.getGesture()
    if g is None:
        continue

    # TODO: return both these from just one method?
    menuSelection, menuOption = gm.getSelectedItem(), gm.getSelectedOption()

    print(f"Got a gesture @ {i}; Do something with {menuSelection} / {menuOption}")

    