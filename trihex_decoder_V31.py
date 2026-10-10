import os
import struct
import math
import cv2
import numpy as np

# ============================================================
# TRI-HEX V3.1 DECODER
# ============================================================

COLOR_TO_BITS = {
    "R": "000",
    "G": "001",
    "B": "010",
    "C": "011",
    "M": "100",
    "Y": "101",
    "K": "110",
    "W": "111",
}

TARGET_COLORS = {
    "R": np.array([255, 0, 0]),
    "G": np.array([0, 255, 0]),
    "B": np.array([0, 0, 255]),
    "C": np.array([0, 255, 255]),
    "M": np.array([255, 0, 255]),
    "Y": np.array([255, 255, 0]),
    "K": np.array([0, 0, 0]),
    "W": np.array([255, 255, 255]),
}

# ============================================================
# SETTINGS
# ============================================================

HEX_RADIUS = 12

X_STEP = HEX_RADIUS * 1.5

Y_STEP = HEX_RADIUS * math.sqrt(3)

COLUMNS = 100

DATA_START_X = 180
DATA_START_Y = 180


# ============================================================
# LOAD IMAGE
# ============================================================

filename = input(
    "Enter Tri-Hex V3.1 image: "
).strip()

if not os.path.exists(filename):

    print("File not found.")
    exit()

image = cv2.imread(filename)

if image is None:

    print("Could not open image.")
    exit()

image_rgb = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2RGB
)

height, width = image.shape[:2]

print(
    "Image:",
    width,
    "x",
    height
)


# ============================================================
# COLOR CLASSIFIER
# ============================================================

def nearest_color(rgb):

    rgb = np.array(
        rgb,
        dtype=float
    )

    best_color = None

    best_distance = float(
        "inf"
    )

    for name, target in TARGET_COLORS.items():

        target = target.astype(float)

        distance = np.linalg.norm(
            rgb - target
        )

        if distance < best_distance:

            best_distance = distance
            best_color = name

    return best_color


# ============================================================
# SAMPLE CENTER
# ============================================================

def sample_color(cx, cy):

    radius = 4

    x1 = max(
        0,
        int(cx - radius)
    )

    x2 = min(
        width,
        int(cx + radius + 1)
    )

    y1 = max(
        0,
        int(cy - radius)
    )

    y2 = min(
        height,
        int(cy + radius + 1)
    )

    region = image_rgb[
        y1:y2,
        x1:x2
    ]

    if region.size == 0:

        return None

    average = np.mean(
        region.reshape(-1, 3),
        axis=0
    )

    return nearest_color(
        average
    )


# ============================================================
# READ FIRST DATA CELL
#
# We know the geometry from the encoder.
# ============================================================

first_color = sample_color(
    DATA_START_X,
    DATA_START_Y
)

print(
    "First detected cell:",
    first_color
)

if first_color is None:

    print("Could not read data.")
    exit()


# ============================================================
# READ ALL DATA CELLS
#
# IMPORTANT:
# We don't know the exact cell count yet.
# So read until image boundary.
# Header will tell us the real file size.
# ============================================================

color_sequence = []

max_rows = int(
    (height - DATA_START_Y) /
    Y_STEP
) + 1

for row in range(max_rows):

    for col in range(COLUMNS):

        x = (
            DATA_START_X +
            col * X_STEP
        )

        y = (
            DATA_START_Y +
            row * Y_STEP
        )

        if row % 2 == 1:

            x += X_STEP / 2

        if (
            x < 0 or
            x >= width or
            y < 0 or
            y >= height
        ):
            continue

        color = sample_color(
            x,
            y
        )

        if color is not None:

            color_sequence.append(
                color
            )


print(
    "Detected cells:",
    len(color_sequence)
)


# ============================================================
# COLORS → BITS
# ============================================================

binary = ""

for color in color_sequence:

    binary += COLOR_TO_BITS[color]


# ============================================================
# BITS → BYTES
# ============================================================

usable_bits = (
    len(binary) -
    len(binary) % 8
)

binary = binary[
    :usable_bits
]

raw = bytearray()

for i in range(
    0,
    len(binary),
    8
):

    raw.append(
        int(
            binary[i:i + 8],
            2
        )
    )


# ============================================================
# SEARCH FOR HEADER
#
# This makes debugging much easier.
# ============================================================

magic = b"THX31"

header_position = raw.find(
    magic
)

if header_position == -1:

    print()
    print("================================")
    print("ERROR")
    print("THX31 HEADER NOT FOUND")
    print("================================")

    print()
    print(
        "The geometry/color sampling is still wrong."
    )

    exit()


print(
    "THX31 header found at:",
    header_position
)


# ============================================================
# READ HEADER
# ============================================================

position = (
    header_position +
    len(magic)
)

version = raw[position]

position += 1

file_size = struct.unpack(
    ">Q",
    raw[
        position:
        position + 8
    ]
)[0]

position += 8

name_length = struct.unpack(
    ">H",
    raw[
        position:
        position + 2
    ]
)[0]

position += 2

name_bytes = raw[
    position:
    position + name_length
]

position += name_length

try:

    file_name = name_bytes.decode(
        "utf-8"
    )

except UnicodeDecodeError:

    print(
        "Filename could not be decoded."
    )

    exit()


# ============================================================
# FILE DATA
# ============================================================

file_data = raw[
    position:
    position + file_size
]


# ============================================================
# CHECK SIZE
# ============================================================

if len(file_data) != file_size:

    print()
    print(
        "WARNING: incomplete data."
    )

    print(
        "Expected:",
        file_size
    )

    print(
        "Recovered:",
        len(file_data)
    )

else:

    print()
    print(
        "Data size verified."
    )


# ============================================================
# SAVE
# ============================================================

output = (
    "decoded_" +
    file_name
)

with open(
    output,
    "wb"
) as f:

    f.write(file_data)


# ============================================================
# RESULT
# ============================================================

print()
print("================================")
print("TRI-HEX V3.1 DECODER")
print("================================")

print(
    "Filename:",
    file_name
)

print(
    "Expected:",
    file_size,
    "bytes"
)

print(
    "Recovered:",
    len(file_data),
    "bytes"
)

print(
    "Output:",
    output
)

if len(file_data) == file_size:

    print()
    print("SUCCESS!")

else:

    print()
    print("FAILED")