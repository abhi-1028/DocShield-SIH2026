import cv2

# Load the document image
image = cv2.imread("sample/yoimage.png")

# Check whether the image was loaded
if image is None:
    print("❌ Image could not be loaded")
else:
    print("✅ Image loaded successfully!")
    print("Image dimensions:", image.shape)