import os
import json

# Disable oneDNN
os.environ["FLAGS_use_mkldnn"] = "0"

from paddleocr import PaddleOCR

# Create OCR object
ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

# Input image
image_path = "sample/straight_document.png"

print("🔍 Running OCR...")
print()

# Run OCR
result = ocr.predict(image_path)

# Store OCR information
ocr_data = []

for res in result:

    # Get recognized text
    texts = res["rec_texts"]

    # Get bounding boxes
    boxes = res["rec_boxes"]

    # Store text and its bounding box
    for text, box in zip(texts, boxes):

        x1, y1, x2, y2 = box.tolist()

        ocr_data.append({
            "text": text,
            "box": [x1, y1, x2, y2]
        })


# Save OCR information to JSON
with open("ocr_results.json", "w", encoding="utf-8") as file:
    json.dump(ocr_data, file, indent=4)


# Display extracted text
print("===== EXTRACTED TEXT =====")
print()

for item in ocr_data:
    print(item["text"])

print()
print("===== OCR DATA SAVED =====")
print()

print("Saved to: ocr_results.json")

print()
print("✅ OCR completed!")