import time
import busio
import board
import digitalio

# The person sensor has the I2C ID of hex 62, or decimal 98.
SENSOR_I2C_ADDRESS = 0x62

# Sensor data length in bytes.
SENSOR_DATA_BYTE_COUNT = 13

# How long to pause between sensor polls.
SENSOR_DELAY = 0.2

# These pins are for the Pico. Other boards will need different constants,
# or you may just be able to call board.i2c() directly.
i2c = busio.I2C(scl=board.GP1, sda=board.GP0)

# Wait until we can access the bus.
while not i2c.try_lock():
    pass

# For debugging purposes print out the peripheral addresses on the I2C bus.
# 98 (0x62 in hex) is the address of our person sensor, and should be
# present in the list.
print(i2c.scan())

# We're going to use the LED for output.
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

while True:
    read_data = bytearray(SENSOR_DATA_BYTE_COUNT)
    i2c.readfrom_into(SENSOR_I2C_ADDRESS, read_data)
    print(read_data)
    time.sleep(SENSOR_DELAY)
