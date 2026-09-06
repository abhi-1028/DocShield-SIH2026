import cv2
import numpy as np

# Load the original document image
image = cv2.imread("sample/ulalapancard.jpeg")

if image is None:
    print("❌ Could not load the image!")
    exit()

print("Original image:", image.shape)


# Convert image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

print("Grayscale image:", gray.shape)


# Blur the image to remove noise
blurred = cv2.GaussianBlur(
    gray,
    (5, 5),
    0
)

print("Blurred image:", blurred.shape)


# Detect edges
edges = cv2.Canny(
    blurred,
    50,
    150
)

print("Edges image:", edges.shape)


# Find contours
contours, _ = cv2.findContours(
    edges,
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_SIMPLE
)

print("Number of contours found:", len(contours))


# Sort contours by area
contours = sorted(
    contours,
    key=cv2.contourArea,
    reverse=True
)


document_corners = None


# Look for a rectangular document boundary
for contour in contours:

    perimeter = cv2.arcLength(
        contour,
        True
    )

    approximation = cv2.approxPolyDP(
        contour,
        0.02 * perimeter,
        True
    )

    # A document boundary normally has 4 corners
    if len(approximation) == 4:

        document_corners = approximation.reshape(4, 2)

        break


# Check whether a document was found
if document_corners is not None:

    print("✅ Document boundary detected!")

    print("Document corners:")
    print(document_corners)

    # Draw detected boundary
    boundary_image = image.copy()

    cv2.drawContours(
        boundary_image,
        [document_corners.reshape(-1, 1, 2)],
        -1,
        (0, 255, 0),
        3
    )

    # Save boundary image
    cv2.imwrite(
        "sample/document_boundary.png",
        boundary_image
    )

    print("✅ Boundary image saved!")

else:

    print("❌ Document boundary not detected!")