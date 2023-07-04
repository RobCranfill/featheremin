import board
import adafruit_vl53l0x
import digitalio as feather_digitalio
import time

L0X_A_RESET_OUT = board.D4
L0X_B_ALTERNATE_I2C_ADDR = 0x31


# I2C addresses
#   VL53L0X         0x29        can change via software
#   Rotary          0x36        can change via jumper
#   APDC9660        0x39        fixed

def showI2Cbus():
    i2c = board.I2C()
    if i2c.try_lock():
        print(f"{[hex(x) for x in i2c.scan()]}")
        i2c.unlock()

# Easist way to init I2C on a Feather:
i2c = board.STEMMA_I2C()

print("Bus to start: ")
showI2Cbus()


# ----------------- 'Primary' VL53L0X time-of-flight sensor 
# We have wired a GPIO line to this sensor so we can temporarily turn it off.
# We will finish setting this sensor up after we init the 'secondary' ToF sensor.

# Turn off the ToF sensor - take XSHUT pin low
print("Turning off primary VL53L0X...")
L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
L0X_A_reset.value = 0
# primary VL53L0X sensor is now turned off
print("After turning off primary: ")
showI2Cbus()


# ----------------- 'Secondary' VL53L0X time-of-flight sensor
# 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
# First, see if it's there with the new address (left over from a previous run).
# If so, we don't need to re-assign it.
try:
    L0X_B = adafruit_vl53l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
    print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
except:
    print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
    try:
        L0X_B = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
        print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
        L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
        print("VL53L0X set_address OK")

        # # # set non-default values?
        # L0X_B.inter_measurement = 0
        # L0X_B.timing_budget = 100
        # L0X_B.start_ranging()

        # print("--------------------")
        # print("VL53L4CD:")
        # model_id, module_type = L4CD.model_info
        # print(f"    Model ID: 0x{model_id:0X}")
        # print(f"    Module Type: 0x{module_type:0X}")
        # print(f"    Timing Budget: {L4CD.timing_budget}")
        # print(f"    Inter-Measurement: {L4CD.inter_measurement}")
        # print("--------------------")
        print("secondary VL53L0X init OK")
    except:
        print("**** No secondary VL53L0X?")
        L0X_B = None


# ----------------- VL53L0X time-of-flight sensor, part 2
# Turn L0X back on and instantiate its object
print("Turning VL53L0X back on...")
L0X_A_reset.value = 1
try:
    L0X_A = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
    print("'Primary' VL53L0X init OK")

    # a higher speed but less accurate timing budget of 20ms:
    L0X_A.measurement_timing_budget = 20000


except:
    print("**** No primary VL53L0X? Continuing....")

# Show bus again?
showI2Cbus()


while True:
    r1 = -1
    if L0X_A:
        r1 = L0X_A.range
    r2 = -1
    if L0X_B:
        r2 = L0X_B.range

    print(f"({r1}, {r2})")
    time.sleep(.1)