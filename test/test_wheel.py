

import board
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel

i2c = board.I2C()  # uses board.SCL and board.SDA
if i2c.try_lock():
    print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
    i2c.unlock()
    
qt_enc = seesaw.Seesaw(i2c, addr=0x36)

qt_enc.pin_mode(24, qt_enc.INPUT_PULLUP)
button = digitalio.DigitalIO(qt_enc, 24)
button_held = False

encoder = rotaryio.IncrementalEncoder(qt_enc)
last_position = None

pixel = neopixel.NeoPixel(qt_enc, 6, 1)
pixel.brightness = 0.01
pixel.fill(0xff0000)

while True:

    buttonPressed = not button.value

    # negate the position to make clockwise rotation positive
    position = -encoder.position

    if position != last_position:
        last_position = position
        print(f"Position: {position}")

    if buttonPressed and not button_held:
        button_held = True
        pixel.brightness = 0.5
        print("Button pressed")

    if not buttonPressed and button_held:
        button_held = False
        pixel.brightness = 0.2
        print("Button released")
