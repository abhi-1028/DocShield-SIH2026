import cv2
import numpy as np
import json


# ============================================================
# DOCSHIELD - PERSPECTIVE CORRECTION
# ============================================================

IMAGE_PATH = "uploads/input_document.jpg"
CORNERS_PATH = "sample/document_corners.json"
OUTPUT_PATH = "sample/straight_document.png"


# ============================================================
# LOAD IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Could not load document image!")
    exit(1)


# ============================================================
# LOAD CORNERS
# ============================================================

try:

    with open(
        CORNERS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    points = np.float32(
        data["corners"]
    )

except Exception as error:

    print("ERROR: Could not load document corners!")
    print(error)
    exit(1)


print("Document corners loaded:")
print(points)


# ============================================================
# ORDER CORNERS
# ============================================================

def order_points(points):

    rectangle = np.zeros(
        (4, 2),
        dtype=np.float32
    )

    total = points.sum(axis=1)

    rectangle[0] = points[np.argmin(total)]
    rectangle[2] = points[np.argmax(total)]

    difference = np.diff(
        points,
        axis=1
    )

    rectangle[1] = points[np.argmin(difference)]
    rectangle[3] = points[np.argmax(difference)]

    return rectangle


points = order_points(points)

print("Ordered corners:")
print(points)


# ============================================================
# CALCULATE SIZE
# ============================================================

top_width = np.linalg.norm(
    points[1] - points[0]
)

bottom_width = np.linalg.norm(
    points[2] - points[3]
)

left_height = np.linalg.norm(
    points[3] - points[0]
)

right_height = np.linalg.norm(
    points[2] - points[1]
)


width = int(
    max(
        top_width,
        bottom_width
    )
)

height = int(
    max(
        left_height,
        right_height
    )
)


width = max(width, 100)
height = max(height, 100)


# ============================================================
# DESTINATION
# ============================================================

destination = np.float32([
    [0, 0],
    [width - 1, 0],
    [width - 1, height - 1],
    [0, height - 1]
])


# ============================================================
# TRANSFORMATION
# ============================================================

matrix = cv2.getPerspectiveTransform(
    points,
    destination
)


warped = cv2.warpPerspective(
    image,
    matrix,
    (width, height)
)


# ============================================================
# SAVE
# ============================================================

cv2.imwrite(
    OUTPUT_PATH,
    warped
)


print()
print("Original image:", image.shape)
print("Corrected image:", warped.shape)
print("Perspective correction completed!")
print("Saved:", OUTPUT_PATH)