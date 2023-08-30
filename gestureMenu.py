'''
    Class GestureMenu (& ancillary classes)
    
    Display a user menu and uses a APDS9960 gesture sensor to access it.

    TODO:
        - implement range options
        - be able to pre-select an option other than the first
            (this is perhaps less important for normal items; moreso for range items such as volume)

'''
import board
from adafruit_apds9960.apds9960 import APDS9960
import feathereminDisplay3 as featherDisplay


class MenuItem():
    def __init__(self, itemStr, optionsList, optionIndex):
        self._itemStr = itemStr
        self._optionsList = optionsList
        self._selectedOption = optionsList[optionIndex]
        self._isActive = False

    def selectNextOption(self):
        i = (self._optionsList.index(self._selectedOption) + 1) % len(self._optionsList)
        self._selectedOption = self._optionsList[i]

    def selectPrevOption(self):
        i = (self._optionsList.index(self._selectedOption) - 1) % len(self._optionsList)
        self._selectedOption = self._optionsList[i]
# end class MenuItem

class MenuHandler():
    '''
        Handle changes in selection, and returning selections.
    '''
    def __init__(self, menuListData) -> None:

        # dictionary that includes user selection
        self._stateDict = {}
        self._itemList = []
        self._selectedItemKey = None
        for mItem in menuListData:

            itemName = mItem[0]
            optionsList = mItem[1]
            optionDefaultIndex = mItem[2]

            self._stateDict[itemName] = MenuItem(itemName, optionsList, optionDefaultIndex)
            self._itemList.append(itemName)

            # set first item as active - FIXME use specified defaults
            if self._selectedItemKey is None:
                self._selectedItemKey = itemName

        # we will only need to report back events that changed an option 
        # (not ones that only changed the sected item)
        self._optionChanged = False

        # print(f"Dictionary: {self._stateDict}\n")
        # print(f"Items: {self._itemList}")


    def getItems(self):
        '''
        list of all top-level menu 'items' (the keys thereto), in defined order (as we want in the menu list)
        '''
        return self._itemList

    # the current selected item
    def getSelectedItem(self):
        return self._selectedItemKey

    # FIXME: why is this here? why isn't it needed? i'm so confused....
    # def getSelectedOption(self):
    #     self._stateDict[self._selectedItemKey]._selectedOption

    # the current option for the given item
    def getItemOption(self, keyStr):
        if keyStr is None:
            return "?"
        return self._stateDict[keyStr]._selectedOption
    
    # list of all
    def getOptionsForItem(self, keyStr):
        return self._stateDict[keyStr]._optionsList

    # select next item, wrapping
    def selectNextItem(self):
        i = (self._itemList.index(self._selectedItemKey) + 1) % len(self._itemList)
        self._selectedItemKey = self._itemList[i]
        self._optionChanged = False

    # select prev item, wrapping
    def selectPrevItem(self):
        i = (self._itemList.index(self._selectedItemKey) - 1) % len(self._itemList)
        self._selectedItemKey = self._itemList[i]
        self._optionChanged = False

    # set selected option to the next one in the list, wrapping
    def setNextOption(self):
        mi = self._stateDict[self._selectedItemKey]
        mi.selectNextOption()
        self._optionChanged = True

    # set selected option to the prev one in the list, wrapping
    def setPrevOption(self):
        mi = self._stateDict[self._selectedItemKey]
        mi.selectPrevOption()
        self._optionChanged = True

# end class MenuHandler


class GestureMenu:
    '''
    Display a menu and update it based on gestures from a APDS9960.

    '''
    def __init__(self, gestureSensor, display, menuData, windowSize=3):

        self._apds = gestureSensor
        self._display = display
        self._windowSize = windowSize

        # FIXME: the calling code should do this?
        try:
            self._apds.enable_gesture = True
            self._apds.enable_proximity = True # must be True even for use only as gesture sensor
            self._apds.rotation = 0 # this is correct for my upside-down test setup at OS; was 90 (?!)
            # print("APDS9960 init OK")
        except:
            print("**** No APDS9960 gesture sensor? Continuing....")

        self._menuHandler = MenuHandler(menuData)
        self.updateDisplay()

    # end GestureMenu.__init__


    def updateDisplay(self):
        '''
            Display {windowSize} items, with the selected one in the 2nd position (index 1).
        '''
        allKeys = self._menuHandler.getItems()

        # find the keys of the menu items to display
        # build a list of the keys, twice
        keyList = []
        for k in allKeys:
            keyList.append(k)
        for k in allKeys:
            keyList.append(k)
        
        # print(f"displaying {self._windowSize} items")

        startLookingAt = 1 # not quite right?
        kLoc = keyList.index(self.getSelectedItem(), startLookingAt)
        displayKeys = keyList[kLoc-1:kLoc+self._windowSize-1]

        # something is wrong here, I think. Works now. Broke with windowSize 3?
        for i in range(self._windowSize):
            # print(f" item {i} key: {displayKeys[i]}")
            self._display.setTextAreaN(i, f"{displayKeys[i]} = {self.getItemOption(displayKeys[i])}")


    def getItemAndOption(self):
        '''
            Look for a gesture and update the menu accordingly.
            If an option was changed, return the item and option.
            If only the selected item was changed, return (None, None)
        '''
        g = self.getGesture()
        if g is None:
            return None, None
        if self._menuHandler._optionChanged is False:
            return None, None
        si = self._menuHandler.getSelectedItem()
        return si, self._menuHandler.getItemOption(si)

    # the menu item whose value changed
    def getSelectedItem(self):
        return self._menuHandler.getSelectedItem()
    
    # current option value for changed menu item
    def getSelectedOption(self):
        return self._menuHandler.getItemOption(self.getSelectedItem())
    
    # current option value for given menu item
    def getItemOption(self, itemStr):
        return self._menuHandler.getItemOption(itemStr)

    # get a gesture, if any; if so, update menu
    # only return gestures that 
    def getGesture(self):

        g = self._apds.gesture()
        if g == 0:
            return None
        
        if g == 1: # down
            self._menuHandler.selectNextItem()
        elif g == 2: # up
            self._menuHandler.selectPrevItem()
        elif g == 3: # left
            self._menuHandler.setPrevOption()
        elif g == 4: # right
            self._menuHandler.setNextOption()

        self.updateDisplay()

        return g
        # end getGesture


    def test(self):
        print("Test/demo GestureMenu!")
        i = 0
        while True:
            i += 1

            # # works but not quite what we need
            # g = self.getGesture()
            # if g is None:
            #     continue
            # # TODO: return both these from just one method?
            # menuSelection, menuOption = self.getSelectedItem(), self.getSelectedOption()
            # print(f"Got a gesture @ {i}; Do something with {menuSelection} / {menuOption}")


            item, option = self.getItemAndOption()
            if item is None:
                continue
            print(f"Got a gesture @ {i}; Do something with {item} / {option}")

        while True:
            pass

    # end class GestureMenu
