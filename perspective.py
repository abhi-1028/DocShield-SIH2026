import cv2
import numpy as np

# Load the original document image
image = cv2.imread("sample/yoimage.png")

if image is None:
    print("❌ Image could not be loaded!")
    exit()

# Document corners detected by preprocess.py
# Order: top-left, top-right, bottom-right, bottom-left
points = np.float32([
    [186, 151],
    [613, 151],
    [613, 579],
    [186, 579]
])

# Desired output size
width = 427
height = 428

# Destination points
destination = np.float32([
    [0, 0],
    [width - 1, 0],
    [width - 1, height - 1],
    [0, height - 1]
])

# Calculate perspective transformation
matrix = cv2.getPerspectiveTransform(points, destination)

# Apply perspective correction
warped = cv2.warpPerspective(
    image,
    matrix,
    (width, height)
)

# Save corrected document
cv2.imwrite("sample/straight_document.png", warped)

print("Original image:", image.shape)
print("Corrected image:", warped.shape)
print("✅ Perspective correction completed!")
print("✅ Saved as sample/straight_document.png")