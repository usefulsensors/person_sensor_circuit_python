# Example of accessing the Person Sensor from Useful Sensors on a Pico using
# CircuitPython. See https://usfl.ink/ps_dev for the full developer guide.

import bitmaptools
import board
import busio
import digitalio
import displayio
import struct
import time

# The person sensor has the I2C ID of hex 62, or decimal 98.
PERSON_SENSOR_I2C_ADDRESS = 0x62

# We will be reading raw bytes over I2C, and we'll need to decode them into
# data structures. These strings define the format used for the decoding, and
# are derived from the layouts defined in the developer guide.
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
    PERSON_SENSOR_I2C_HEADER_FORMAT)

PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
    "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)

# How long to pause between sensor polls.
PERSON_SENSOR_DELAY = 0.2

# The Pico doesn't support board.I2C(), so check before calling it. If it isn't
# present then we assume we're on a Pico and call an explicit function.
try:
    i2c = board.I2C()
except:
    i2c = busio.I2C(scl=board.GP5, sda=board.GP4)

# Wait until we can access the bus.
while not i2c.try_lock():
    pass

# For debugging purposes print out the peripheral addresses on the I2C bus.
# 98 (0x62 in hex) is the address of our person sensor, and should be
# present in the list. Uncomment the following three lines if you want to see
# what I2C addresses are found.
# while True:
#    print(i2c.scan())
#    time.sleep(PERSON_SENSOR_DELAY)

# Set up the builtin display if there's one available
try:
    display = board.DISPLAY
except:
    display = None
if display:
    bitmap = displayio.Bitmap(display.width, display.height, 2)
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0xffffff
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile_grid)
    display.show(group)

# Keep looping and reading the person sensor results.
while True:
    read_data = bytearray(PERSON_SENSOR_RESULT_BYTE_COUNT)
    i2c.readfrom_into(PERSON_SENSOR_I2C_ADDRESS, read_data)

    offset = 0
    (pad1, pad2, payload_bytes) = struct.unpack_from(
        PERSON_SENSOR_I2C_HEADER_FORMAT, read_data, offset)
    offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

    (num_faces) = struct.unpack_from("B", read_data, offset)
    num_faces = int(num_faces[0])
    offset = offset + 1

    faces = []
    for i in range(num_faces):
        (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
         is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_data, offset)
        offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
        face = {
            "box_confidence": box_confidence,
            "box_left": box_left,
            "box_top": box_top,
            "box_right": box_right,
            "box_bottom": box_bottom,
            "id_confidence": id_confidence,
            "id": id,
            "is_facing": is_facing,
        }
        faces.append(face)
    checksum = struct.unpack_from("H", read_data, offset)
    print(num_faces, faces)

    # If the board has a display, draw rectangles for the face boxes, and a
    # diagonal cross if the person is facing the sensor.
    if display:
        bitmaptools.fill_region(bitmap, 0, 0, display.width, display.height, 0)
        for face in faces:
            box_left = face["box_left"]
            box_top = face["box_top"]
            box_right = face["box_right"]
            box_bottom = face["box_bottom"]
            x0 = int((box_left * display.width) / 256)
            y0 = int((box_top * display.height) / 256)
            x1 = int((box_right * display.width) / 256)
            y1 = int((box_bottom * display.height) / 256)
            print(x0, y0, x1, y1)
            print(display.width, display.height)
            bitmaptools.draw_line(bitmap, x0, y0, x1, y0, 1)
            bitmaptools.draw_line(bitmap, x1, y0, x1, y1, 1)
            bitmaptools.draw_line(bitmap, x1, y1, x0, y1, 1)
            bitmaptools.draw_line(bitmap, x0, y1, x0, y0, 1)
            if face["is_facing"]:
                bitmaptools.draw_line(bitmap, x0, y0, x1, y1, 1)
                bitmaptools.draw_line(bitmap, x1, y0, x0, y1, 1)

    time.sleep(PERSON_SENSOR_DELAY)
