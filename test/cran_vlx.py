import board
import digitalio as feather_digitalio

import adafruit_vl53l0x as vl52l0x


class CranVLX:

    def __init__(self) -> None:

        L0X_A_RESET_OUT = board.D4
        L0X_B_ALTERNATE_I2C_ADDR = 0x30

        self._sensor_A = None
        self._sensor_B = None
        
        try:
            i2c = board.STEMMA_I2C()
        except:
            print("board.STEMMA_I2C failed! Is the Stemma bus connected? It would seem not.")
            return
        
        # ----------------- VL53L0X time-of-flight sensor 
        # We will finish setting this sensor up 
        # *after* we turn it off and init the 'secondary' ToF sensor.
        
        # Turn off the ToF sensor - take XSHUT pin low
        print("Turning off primary VL53L0X...")
        L0X_A_reset = feather_digitalio.DigitalInOut(L0X_A_RESET_OUT)
        L0X_A_reset.direction = feather_digitalio.Direction.OUTPUT
        L0X_A_reset.value = False
        # VL53L0X sensor is now turned off
        showI2Cbus()


        # ----------------- VL53L4CD time-of-flight sensor
        # 'Secondary' ToF - the one DIDN'T wire the XSHUT pin to.
        # First, see if it's there with the new address (left over from a previous run).
        # If so, we don't need to re-assign it.
        try:
            L0X_B = vl52l0x.VL53L0X(i2c, address=L0X_B_ALTERNATE_I2C_ADDR)
            print(f"Found secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}; OK")
        except:
            print(f"Did not find secondary VL53L0X at {hex(L0X_B_ALTERNATE_I2C_ADDR)}, trying default....")
            try:
                # Try at the default address
                L0X_B = adafruit_vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check
                print(f"Found VL53L0X at default address; setting to {hex(L0X_B_ALTERNATE_I2C_ADDR)}...")
                L0X_B.set_address(L0X_B_ALTERNATE_I2C_ADDR)  # address assigned should NOT be already in use
                print("VL53L0X set_address OK")

                # Set params for the sensor?
                # # The default timing budget is 33ms, a good compromise of speed and accuracy.
                # # For example a higher speed but less accurate timing budget of 20ms:
                # L0X_B.measurement_timing_budget = 20000
                # # Or a slower but more accurate timing budget of 200ms:
                # L0X_B.measurement_timing_budget = 200000

                print("Secondary VL53L0X init OK")
            except Exception as e:
                print(f"**** Caught exception: {e}")
                print("**** No secondary VL53L0X?")
                L0X_B = None


        # ----------------- VL53L0X time-of-flight sensor, part 2
        # Turn L0X back on and instantiate its object
        print("Turning VL53L0X back on...")
        L0X_A_reset.value = True
        L0X_A = None
        try:
            L0X_A = vl53l0x.VL53L0X(i2c)  # also performs VL53L0X hardware check

            # Set params for the sensor?
            # # The default timing budget is 33ms, a good compromise of speed and accuracy.
            # # For example a higher speed but less accurate timing budget of 20ms:
            # L0X_A.measurement_timing_budget = 20000
            # # Or a slower but more accurate timing budget of 200ms:
            # L0X_A.measurement_timing_budget = 200000

            print("'Primary' VL53L0X init OK")
        except:
            print("**** No primary VL53L0X? Continuing....")

        # Show bus again?
        showI2Cbus()


        self._sensor_A = L0X_A
        self._sensor_B = L0X_B


    def getSensors(self) -> (vl52l0x.VL53L0X, vl52l0x.VL53L0X):

        return self._sensor_A, self._sensor_B

    
    def showI2Cbus():
        i2c = board.I2C()
        if i2c.try_lock():
            print(f"I2C addresses found: {[hex(x) for x in i2c.scan()]}")
            i2c.unlock()
