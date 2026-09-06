import cv2
import numpy as np
import json


# ============================================================
# DOCSHIELD - DOCUMENT PREPROCESSING
# ============================================================

IMAGE_PATH = "uploads/input_document.jpg"

BOUNDARY_OUTPUT = "sample/document_boundary.png"
EDGES_OUTPUT = "sample/edges.png"
CORNERS_OUTPUT = "sample/document_corners.json"


# ============================================================
# LOAD IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Could not load document image!")
    print("Expected:", IMAGE_PATH)
    exit(1)

print("Original image:", image.shape)


# ============================================================
# GRAYSCALE
# ============================================================

gray = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2GRAY
)

print("Grayscale image:", gray.shape)


# ============================================================
# GAUSSIAN BLUR
# ============================================================

blurred = cv2.GaussianBlur(
    gray,
    (5, 5),
    0
)

print("Blurred image:", blurred.shape)


# ============================================================
# CANNY EDGE DETECTION
# ============================================================

edges = cv2.Canny(
    blurred,
    50,
    150
)

print("Edges image:", edges.shape)

cv2.imwrite(
    EDGES_OUTPUT,
    edges
)


# ============================================================
# CONTOURS
# ============================================================

contours, _ = cv2.findContours(
    edges,
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_SIMPLE
)

print("Number of contours found:", len(contours))


# ============================================================
# FIND DOCUMENT BOUNDARY
# ============================================================

image_height, image_width = gray.shape
image_area = image_height * image_width

minimum_area = image_area * 0.10

best_area = 0
document_corners = None


contours = sorted(
    contours,
    key=cv2.contourArea,
    reverse=True
)


for contour in contours:

    area = cv2.contourArea(contour)

    if area < minimum_area:
        continue

    perimeter = cv2.arcLength(
        contour,
        True
    )

    if perimeter == 0:
        continue

    approximation = cv2.approxPolyDP(
        contour,
        0.02 * perimeter,
        True
    )

    if len(approximation) != 4:
        continue

    x, y, w, h = cv2.boundingRect(
        approximation
    )

    if w < 30 or h < 30:
        continue

    # Reject extremely thin rectangles
    aspect_ratio = w / float(h)

    if aspect_ratio > 10 or aspect_ratio < 0.1:
        continue

    if area > best_area:

        best_area = area

        document_corners = (
            approximation
            .reshape(4, 2)
            .astype(np.float32)
        )


# ============================================================
# FALLBACK
# ============================================================

if document_corners is None:

    print()
    print("WARNING: No reliable document boundary detected.")
    print("Using the entire image as the document.")

    document_corners = np.float32([
        [0, 0],
        [image_width - 1, 0],
        [image_width - 1, image_height - 1],
        [0, image_height - 1]
    ])

    boundary_image = image.copy()

    print("Full-image document boundary selected.")

else:

    print()
    print("Document boundary detected!")
    print("Document area:", best_area)

    print("Document corners:")
    print(document_corners)

    boundary_image = image.copy()

    cv2.drawContours(
        boundary_image,
        [
            document_corners
            .astype(np.int32)
            .reshape(-1, 1, 2)
        ],
        -1,
        (0, 255, 0),
        3
    )


# ============================================================
# SAVE BOUNDARY IMAGE
# ============================================================

cv2.imwrite(
    BOUNDARY_OUTPUT,
    boundary_image
)


# ============================================================
# SAVE CORNERS
# ============================================================

corners_data = {
    "corners": document_corners.tolist()
}


with open(
    CORNERS_OUTPUT,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        corners_data,
        file,
        indent=4
    )


print()
print("Boundary image saved:", BOUNDARY_OUTPUT)
print("Document corners saved:", CORNERS_OUTPUT)
print()
print("Preprocessing completed successfully!")