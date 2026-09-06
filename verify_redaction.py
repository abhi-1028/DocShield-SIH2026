import json
from paddleocr import PaddleOCR


# ============================================================
# DOCSHIELD - REDACTION VERIFICATION
# ============================================================

PROTECTED_IMAGE = "sample/protected_document.png"
DETECTED_DATA_FILE = "detected_data.json"


# ============================================================
# LOAD DETECTED SENSITIVE DATA
# ============================================================

try:

    with open(
        DETECTED_DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        detected_data = json.load(file)

except Exception as error:

    print("ERROR: Could not load detected data!")
    print(error)
    exit()


if not detected_data:

    print("No sensitive information found to verify.")
    exit()


# ============================================================
# RUN OCR ON PROTECTED DOCUMENT
# ============================================================

print("=" * 50)
print("DOCSHIELD - REDACTION VERIFICATION")
print("=" * 50)
print()

print("Scanning protected document...")
print()

ocr = PaddleOCR(lang="en")

result = ocr.predict(PROTECTED_IMAGE)


# ============================================================
# EXTRACT OCR TEXT
# ============================================================

ocr_text = []

for page in result:

    texts = page.get("rec_texts", [])

    for text in texts:

        if text:
            ocr_text.append(text)


# Combine all OCR text
combined_text = " ".join(ocr_text)


# ============================================================
# VERIFY EACH SENSITIVE ITEM
# ============================================================

all_passed = True

for item in detected_data:

    sensitive_type = item.get("type", "UNKNOWN")

    # We intentionally do NOT use the raw sensitive value
    # from detected_data.json.
    #
    # Instead, verification checks whether OCR can detect
    # the sensitive pattern again.

    import re

    if sensitive_type == "PAN":

        pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

    elif sensitive_type == "AADHAAR":

        pattern = r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"

    elif sensitive_type == "PHONE":

        pattern = r"\b(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"

    elif sensitive_type == "EMAIL":

        pattern = r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"

    elif sensitive_type == "DOB":

        pattern = (
            r"\b(?:"
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
            r"|"
            r"\d{1,2}\s+[A-Za-z]+\s+\d{4}"
            r")\b"
        )

    else:

        print(f"Unknown sensitive type: {sensitive_type}")
        continue


    # Search OCR output for sensitive pattern

    match = re.search(
        pattern,
        combined_text,
        re.IGNORECASE
    )


    if match:

        print(f"❌ {sensitive_type} verification FAILED")
        print("Sensitive information may still be readable.")
        print(f"OCR detected: {match.group()}")
        print()

        all_passed = False

    else:

        print(f"✅ {sensitive_type} verification PASSED")
        print("Sensitive information is no longer readable.")
        print()


# ============================================================
# FINAL RESULT
# ============================================================

print("=" * 50)

if all_passed:

    print("PROTECTION VERIFICATION SUCCESSFUL ✅")
    print()
    print("The protected document passed OCR verification.")

else:

    print("PROTECTION VERIFICATION FAILED ❌")
    print()
    print("Some sensitive information may still be readable.")

print("=" * 50)