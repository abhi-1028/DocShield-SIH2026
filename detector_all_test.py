import json
import re


# ============================================================
# DOCSHIELD - SENSITIVE DATA DETECTOR
# ============================================================

OCR_RESULTS_FILE = "ocr_all_test.json"
OUTPUT_FILE = "detected_data.json"


# ============================================================
# REGEX PATTERNS
# ============================================================

# Indian PAN
PAN_PATTERN = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
)

# Aadhaar
AADHAAR_PATTERN = re.compile(
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
)

# Indian mobile number
PHONE_PATTERN = re.compile(
    r"\b(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"
)

# Email address
EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE
)

# Common date formats
DOB_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|"
    r"\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\s+\d{4}"
    r")\b",
    re.IGNORECASE
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

PHONE_CONTEXT = [
    "MOBILE",
    "MOBILE NO",
    "MOBILE NUMBER",
    "PHONE",
    "PHONE NO",
    "PHONE NUMBER",
    "CONTACT",
    "CONTACT NO",
    "CONTACT NUMBER"
]

EMAIL_CONTEXT = [
    "EMAIL",
    "EMAIL ID",
    "EMAIL ADDRESS",
    "E-MAIL",
    "E-MAIL ID"
]

DOB_CONTEXT = [
    "DOB",
    "DATE OF BIRTH",
    "BIRTH DATE",
    "BIRTH"
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
# HELPER FUNCTION
# ============================================================

def context_confidence(context_keywords):

    context_found = any(
        keyword in combined_text
        for keyword in context_keywords
    )

    return "high" if context_found else "medium"


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

        confidence = context_confidence(PAN_CONTEXT)

        detected_data.append(
            {
                "type": "PAN",
                "value": pan_value,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print("PAN detected")
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

        # Remove spaces and hyphens
        normalized_aadhaar = re.sub(
            r"[\s-]",
            "",
            aadhaar_value
        )

        # Aadhaar must contain exactly 12 digits
        if len(normalized_aadhaar) != 12:
            continue

        if not normalized_aadhaar.isdigit():
            continue

        confidence = context_confidence(AADHAAR_CONTEXT)

        detected_data.append(
            {
                "type": "AADHAAR",
                "value": normalized_aadhaar,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print("Aadhaar detected")
        print(f"Confidence: {confidence}")
        print(f"Box: {item['box']}")
        print()


# ============================================================
# PHONE NUMBER DETECTION
# ============================================================

for item in ocr_results:

    text = item.get("text", "").strip()

    if not text:
        continue

    phone_match = PHONE_PATTERN.search(text)

    if phone_match:

        phone_value = phone_match.group()

        # Remove spaces, hyphens and +91
        normalized_phone = re.sub(
            r"[\s-]",
            "",
            phone_value
        )

        if normalized_phone.startswith("+91"):
            normalized_phone = normalized_phone[3:]

        # Must be exactly 10 digits
        if len(normalized_phone) != 10:
            continue

        if not normalized_phone.isdigit():
            continue

        # Indian mobile numbers start from 6-9
        if normalized_phone[0] not in "6789":
            continue

        confidence = context_confidence(PHONE_CONTEXT)

        detected_data.append(
            {
                "type": "PHONE",
                "value": normalized_phone,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print("Phone number detected")
        print(f"Confidence: {confidence}")
        print(f"Box: {item['box']}")
        print()


# ============================================================
# EMAIL DETECTION
# ============================================================

for item in ocr_results:

    text = item.get("text", "").strip()

    if not text:
        continue

    email_match = EMAIL_PATTERN.search(text)

    if email_match:

        email_value = email_match.group()

        confidence = context_confidence(EMAIL_CONTEXT)

        detected_data.append(
            {
                "type": "EMAIL",
                "value": email_value,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print("Email detected")
        print(f"Confidence: {confidence}")
        print(f"Box: {item['box']}")
        print()


# ============================================================
# DATE OF BIRTH DETECTION
# ============================================================

for item in ocr_results:

    text = item.get("text", "").strip()

    if not text:
        continue

    dob_match = DOB_PATTERN.search(text)

    if dob_match:

        dob_value = dob_match.group()

        confidence = context_confidence(DOB_CONTEXT)

        detected_data.append(
            {
                "type": "DOB",
                "value": dob_value,
                "box": item["box"],
                "confidence": confidence
            }
        )

        print("Date of Birth detected")
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
