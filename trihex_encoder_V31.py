import os
import struct
import math
from PIL import Image, ImageDraw

# ============================================================
# TRI-HEX V3.1
# ============================================================

COLORS = {
    "R": (255, 0, 0),
    "G": (0, 255, 0),
    "B": (0, 0, 255),
    "C": (0, 255, 255),
    "M": (255, 0, 255),
    "Y": (255, 255, 0),
    "K": (0, 0, 0),
    "W": (255, 255, 255),
}

BITS_TO_COLOR = {
    "000": "R",
    "001": "G",
    "010": "B",
    "011": "C",
    "100": "M",
    "101": "Y",
    "110": "K",
    "111": "W",
}

# ============================================================
# SETTINGS
# ============================================================

HEX_RADIUS = 12
COLUMNS = 100

# Distance between data area and finder patterns
DATA_OFFSET = 90

# Finder pattern consists of multiple hexagons
FINDER_RADIUS = 12

# ============================================================
# HEXAGON
# ============================================================

def hex_points(cx, cy, radius):

    points = []

    for angle in range(0, 360, 60):

        rad = math.radians(angle)

        points.append(
            (
                cx + radius * math.cos(rad),
                cy + radius * math.sin(rad)
            )
        )

    return points


def draw_hex(draw, cx, cy, color):

    draw.polygon(
        hex_points(
            cx,
            cy,
            HEX_RADIUS
        ),
        fill=COLORS[color]
    )


# ============================================================
# UNIQUE FINDER PATTERN
# ============================================================

def draw_finder(draw, cx, cy):

    """
    7-cell finder pattern.

             K
          W  K  W
       K  W  K  W  K
          W  K  W
             K

    The arrangement is deliberately different from
    ordinary data cells.
    """

    positions = [
        (0, -2, "K"),

        (-1, -1, "W"),
        (0, -1, "K"),
        (1, -1, "W"),

        (-2, 0, "K"),
        (-1, 0, "W"),
        (0, 0, "K"),
        (1, 0, "W"),
        (2, 0, "K"),

        (-1, 1, "W"),
        (0, 1, "K"),
        (1, 1, "W"),

        (0, 2, "K")
    ]

    x_step = HEX_RADIUS * 1.5
    y_step = HEX_RADIUS * math.sqrt(3)

    for dx, dy, color in positions:

        x = cx + dx * x_step

        y = cy + dy * y_step

        draw_hex(
            draw,
            x,
            y,
            color
        )


# ============================================================
# FILE
# ============================================================

filename = input(
    "Enter file to encode: "
).strip()

if not os.path.exists(filename):

    print("File not found.")
    exit()

with open(filename, "rb") as f:

    file_data = f.read()

file_size = len(file_data)

file_name = os.path.basename(filename)

name_bytes = file_name.encode("utf-8")

# ============================================================
# BYTES → BITS
# ============================================================

payload = (
    b"THX31" +
    struct.pack(">B", 1) +
    struct.pack(">Q", file_size) +
    struct.pack(">H", len(name_bytes)) +
    name_bytes +
    file_data
)

binary = "".join(
    f"{byte:08b}"
    for byte in payload
)

padding = (
    3 - len(binary) % 3
) % 3

binary += "0" * padding

sequence = []

for i in range(
    0,
    len(binary),
    3
):

    sequence.append(
        BITS_TO_COLOR[
            binary[i:i + 3]
        ]
    )

data_cells = len(sequence)

rows = math.ceil(
    data_cells / COLUMNS
)

# ============================================================
# GEOMETRY
# ============================================================

X_STEP = HEX_RADIUS * 1.5

Y_STEP = HEX_RADIUS * math.sqrt(3)

DATA_START_X = 180
DATA_START_Y = 180

# Finder locations
FINDER_TL = (60, 60)

FINDER_TR = (
    DATA_START_X +
    (COLUMNS - 1) * X_STEP,
    60
)

FINDER_BL = (
    60,
    DATA_START_Y +
    (rows - 1) * Y_STEP
)

# ============================================================
# IMAGE SIZE
# ============================================================

max_x = max(
    FINDER_TR[0],
    DATA_START_X +
    (COLUMNS - 1) * X_STEP
)

max_y = max(
    FINDER_BL[1],
    DATA_START_Y +
    (rows - 1) * Y_STEP
)

image_width = int(
    max_x + 120
)

image_height = int(
    max_y + 120
)

image = Image.new(
    "RGB",
    (
        image_width,
        image_height
    ),
    COLORS["W"]
)

draw = ImageDraw.Draw(image)

# ============================================================
# FINDERS
# ============================================================

draw_finder(
    draw,
    *FINDER_TL
)

draw_finder(
    draw,
    *FINDER_TR
)

draw_finder(
    draw,
    *FINDER_BL
)

# ============================================================
# DATA
# ============================================================

index = 0

for row in range(rows):

    for col in range(COLUMNS):

        if index >= data_cells:
            break

        x = (
            DATA_START_X +
            col * X_STEP
        )

        y = (
            DATA_START_Y +
            row * Y_STEP
        )

        # Offset alternate rows
        if row % 2 == 1:

            x += X_STEP / 2

        draw_hex(
            draw,
            x,
            y,
            sequence[index]
        )

        index += 1

# ============================================================
# METADATA TEXT
# ============================================================

metadata = (
    f"THX31 | "
    f"ROWS={rows} | "
    f"COLS={COLUMNS} | "
    f"CELLS={data_cells}"
)

draw.text(
    (
        20,
        image_height - 35
    ),
    metadata,
    fill=COLORS["K"]
)

# ============================================================
# SAVE
# ============================================================

output = "trihex_v31.png"

image.save(
    output,
    "PNG"
)

print()
print("================================")
print("TRI-HEX V3.1 ENCODER")
print("================================")

print("File:", file_name)
print("File size:", file_size)
print("Data cells:", data_cells)
print("Rows:", rows)
print("Columns:", COLUMNS)
print("Padding:", padding)

print()
print("Output:", output)
print("SUCCESS")