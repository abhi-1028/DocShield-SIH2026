import cv2
import json

# Load the corrected document image
image = cv2.imread("sample/straight_document.png")

if image is None:
    print("❌ Could not load the document image!")
    exit()

# Load detected sensitive information
with open("detected_data.json", "r", encoding="utf-8") as file:
    detected_data = json.load(file)

print("🛡️ Protecting detected sensitive information...")
print()

# Count protected areas
protected_count = 0

# Redact every detected sensitive item
for item in detected_data:

    text_type = item["type"]
    value = item["value"]
    box = item["box"]

    # Get bounding box coordinates
    x1, y1, x2, y2 = box

    # Draw black rectangle over the detected area
    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 0, 0),
        -1
    )

    protected_count += 1

    print(f"🔴 Protected: {text_type} → {value}")


# Save protected document
output_path = "sample/protected_document.png"

cv2.imwrite(output_path, image)

print()
print(f"🔐 Total protected areas: {protected_count}")
print(f"✅ Protected document saved to: {output_path}")