import json
import re


# ============================================================
# DOCSHIELD - SENSITIVE DATA DETECTOR
# ============================================================

OCR_RESULTS_FILE = "ocr_aadhaar_test.json"
OUTPUT_FILE = "detected_data.json"


# ============================================================
# REGEX PATTERNS
# ============================================================

PAN_PATTERN = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
)

AADHAAR_PATTERN = re.compile(
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
)


# ============================================================
# CONTEXT KEYWORDS
# ============================================================

PAN_CONTEXT = [
    "PAN",
    "PERMANENT ACCOUNT NUMBER",
    "INCOME TAX",
    "TAX DEPARTMENT",
    "GOVT. OF INDIA",
    "GOVERNMENT OF INDIA"
]

AADHAAR_CONTEXT = [
    "AADHAAR",
    "AADHAR",
    "UIDAI",
    "UNIQUE IDENTIFICATION"
]


# ============================================================
# LOAD OCR RESULTS
# ============================================================

try:

    with open(
        OCR_RESULTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        ocr_results = json.load(file)

except Exception as error:

    print("ERROR: Could not load OCR results!")
    print(error)
    exit()


print("Scanning OCR results for sensitive information...")
print()


# ============================================================
# COLLECT OCR TEXT
# ============================================================

all_text = []

for item in ocr_results:

    text = item.get("text", "").strip()

    if text:
        all_text.append(text)


combined_text = " ".join(all_text).upper()


# ============================================================
# DETECTION RESULTS
# ============================================================

detected_data = []


# ============================================================
# PAN DETECTION
# ============================================================

for item in ocr_results:

    text = item.get("text", "").strip()

    if not text:
        continue

    pan_match = PAN_PATTERN.search(text.upper())

    if pan_match:

        pan_value = pan_match.group()

        context_found = any(
            keyword in combined_text
            for keyword in PAN_CONTEXT
        )

        confidence = "high" if context_found else "medium"

        detected_data.append(
            {
                "type": "PAN",
                "value": pan_value,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print(f"PAN detected: {pan_value}")
        print(f"Confidence: {confidence}")
        print(f"Box: {item['box']}")
        print()


# ============================================================
# AADHAAR DETECTION
# ============================================================

for item in ocr_results:

    text = item.get("text", "").strip()

    if not text:
        continue

    aadhaar_match = AADHAAR_PATTERN.search(text)

    if aadhaar_match:

        aadhaar_value = aadhaar_match.group()

        # Remove spaces/hyphens for validation/storage
        normalized_aadhaar = re.sub(
            r"[\s-]",
            "",
            aadhaar_value
        )

        # Make sure it is exactly 12 digits
        if len(normalized_aadhaar) != 12:
            continue

        context_found = any(
            keyword in combined_text
            for keyword in AADHAAR_CONTEXT
        )

        confidence = "high" if context_found else "medium"

        detected_data.append(
            {
                "type": "AADHAAR",
                "value": normalized_aadhaar,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print(f"Aadhaar detected: {aadhaar_value}")
        print(f"Confidence: {confidence}")
        print(f"Box: {item['box']}")
        print()


# ============================================================
# RESULTS
# ============================================================

print("===== SENSITIVE INFORMATION DETECTED =====")
print()


if detected_data:

    for item in detected_data:

        print(f"Type: {item['type']}")
        print(f"Value: {item['value']}")
        print(f"Confidence: {item['confidence']}")
        print(f"Box: {item['box']}")
        print()

else:

    print("No sensitive information detected.")


# ============================================================
# SAVE RESULTS
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        detected_data,
        file,
        indent=4
    )


print(
    f"Total sensitive items: {len(detected_data)}"
)

print(
    f"Detection results saved to: {OUTPUT_FILE}"
)

print("Detection completed!")