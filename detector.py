import json
import re


# ============================================================
# DOCSHIELD - FINAL SENSITIVE DATA DETECTOR
# ============================================================

OCR_FILE = "ocr_results.json"
OUTPUT_FILE = "detected_data.json"


# ============================================================
# REGEX PATTERNS
# ============================================================

PATTERNS = {

    # --------------------------------------------------------
    # PAN CARD
    # Example: ABCDE1234F
    # --------------------------------------------------------
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",

    # --------------------------------------------------------
    # AADHAAR
    # Examples:
    # 1234 5678 9012
    # 123456789012
    # --------------------------------------------------------
    "Aadhaar": (
        r"\b"
        r"[2-9][0-9]{3}"
        r"(?:[\s-]?[0-9]{4})"
        r"(?:[\s-]?[0-9]{4})"
        r"\b"
    ),

    # --------------------------------------------------------
    # INDIAN MOBILE NUMBER
    # Examples:
    # 9876543210
    # +91 9876543210
    # 98765-43210
    # --------------------------------------------------------
    "Phone": (
        r"(?<![0-9])"
        r"(?:\+91[\s-]?)?"
        r"[6-9][0-9]{4}[\s-]?[0-9]{5}"
        r"(?![0-9])"
    ),

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------
    "Email": (
        r"\b"
        r"[A-Za-z0-9._%+-]+"
        r"@"
        r"[A-Za-z0-9.-]+"
        r"\."
        r"[A-Za-z]{2,}"
        r"\b"
    ),

    # --------------------------------------------------------
    # DATE
    # Used carefully with DOB context
    # --------------------------------------------------------
    "Date": (
        r"\b(?:"
        r"[0-3]?[0-9][/-][0-1]?[0-9][/-](?:19|20)?[0-9]{2,4}"
        r"|"
        r"(?:19|20)[0-9]{2}[/-][0-1]?[0-9][/-][0-3]?[0-9]"
        r")\b"
    ),

    # --------------------------------------------------------
    # BANK ACCOUNT NUMBER
    # Common Indian account number lengths
    # --------------------------------------------------------
    "Bank Account": (
        r"\b[0-9]{9,18}\b"
    ),

    # --------------------------------------------------------
    # IFSC CODE
    # Example: SBIN0001234
    # --------------------------------------------------------
    "IFSC": (
        r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
    ),

    # --------------------------------------------------------
    # VOTER ID
    # Example: ABC1234567
    # --------------------------------------------------------
    "Voter ID": (
        r"\b[A-Z]{3}[0-9]{7}\b"
    ),

    # --------------------------------------------------------
    # PASSPORT
    # Common Indian passport format
    # Example: A1234567
    # --------------------------------------------------------
    "Passport": (
        r"\b[A-Z][0-9]{7}\b"
    )
}


# ============================================================
# LABEL / CONTEXT PATTERNS
# ============================================================

NAME_PATTERN = re.compile(
    r"\b(?:name|full name|father'?s name|father name|"
    r"mother'?s name|mother name|guardian name)"
    r"\s*[:\-]\s*(.+)",
    re.IGNORECASE
)


ADDRESS_PATTERN = re.compile(
    r"\b(?:address|residential address|permanent address|"
    r"communication address|present address)"
    r"\s*[:\-]\s*(.+)",
    re.IGNORECASE
)


DOB_PATTERN = re.compile(
    r"\b(?:date of birth|dob|birth date|born)"
    r"\s*[:\-]?\s*(.+)",
    re.IGNORECASE
)


BANK_ACCOUNT_LABEL_PATTERN = re.compile(
    r"\b(?:account number|account no|a/c no|a/c number|"
    r"bank account)\s*[:\-]?\s*([0-9]{9,18})\b",
    re.IGNORECASE
)


IFSC_LABEL_PATTERN = re.compile(
    r"\b(?:ifsc|ifsc code)\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})\b",
    re.IGNORECASE
)


# ============================================================
# LOAD OCR RESULTS
# ============================================================

try:

    with open(
        OCR_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        ocr_data = json.load(file)

except Exception as error:

    print("ERROR: Could not load OCR results!")
    print(error)
    exit(1)


print("Scanning OCR results for sensitive information...")
print()


# ============================================================
# DETECTION STORAGE
# ============================================================

detected_items = []


def add_detection(
    data_type,
    value,
    box,
    confidence="medium"
):

    if not value:
        return

    value = str(value).strip()

    if not value:
        return

    if not isinstance(box, list) or len(box) != 4:
        return

    detected_items.append({

        "type": data_type,

        "value": value,

        "box": box,

        "confidence": confidence

    })


# ============================================================
# HELPER - ADD REGEX MATCHES
# ============================================================

def detect_pattern(
    pattern_name,
    text,
    box,
    confidence="high"
):

    pattern = PATTERNS[pattern_name]

    for match in re.finditer(
        pattern,
        text,
        re.IGNORECASE
    ):

        value = match.group(0).strip()

        # ----------------------------------------------------
        # Avoid classifying PAN as other ID types
        # ----------------------------------------------------

        if pattern_name != "PAN":

            if re.fullmatch(
                PATTERNS["PAN"],
                value,
                re.IGNORECASE
            ):

                continue

        # ----------------------------------------------------
        # Avoid classifying IFSC as generic account number
        # ----------------------------------------------------

        if pattern_name == "Bank Account":

            if not value.isdigit():
                continue

        add_detection(
            pattern_name,
            value.upper()
            if pattern_name in ["PAN", "IFSC", "Voter ID"]
            else value,
            box,
            confidence
        )


# ============================================================
# SCAN OCR ITEMS
# ============================================================

for item in ocr_data:

    text = item.get(
        "text",
        ""
    )

    box = item.get(
        "box",
        []
    )

    if not text:
        continue

    clean_text = " ".join(
        str(text).strip().split()
    )

    if not clean_text:
        continue


    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    detect_pattern(
        "PAN",
        clean_text,
        box,
        "high"
    )


    # --------------------------------------------------------
    # AADHAAR
    # --------------------------------------------------------

    for match in re.finditer(
        PATTERNS["Aadhaar"],
        clean_text
    ):

        value = re.sub(
            r"[\s-]",
            "",
            match.group(0)
        )

        add_detection(
            "Aadhaar",
            value,
            box,
            "high"
        )


    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    detect_pattern(
        "Phone",
        clean_text,
        box,
        "high"
    )


    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    detect_pattern(
        "Email",
        clean_text,
        box,
        "high"
    )


    # --------------------------------------------------------
    # IFSC
    # --------------------------------------------------------

    detect_pattern(
        "IFSC",
        clean_text.upper(),
        box,
        "high"
    )


    # --------------------------------------------------------
    # VOTER ID
    # --------------------------------------------------------

    detect_pattern(
        "Voter ID",
        clean_text.upper(),
        box,
        "medium"
    )


    # --------------------------------------------------------
    # PASSPORT
    # --------------------------------------------------------

    # Only detect passport when context exists,
    # to reduce false positives.

    if re.search(
        r"\bpassport\b",
        clean_text,
        re.IGNORECASE
    ):

        detect_pattern(
            "Passport",
            clean_text.upper(),
            box,
            "high"
        )


    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    name_match = NAME_PATTERN.search(
        clean_text
    )

    if name_match:

        name_value = name_match.group(1).strip()

        # Remove obvious trailing labels

        add_detection(
            "Name",
            name_value,
            box,
            "high"
        )


    # --------------------------------------------------------
    # ADDRESS
    # --------------------------------------------------------

    address_match = ADDRESS_PATTERN.search(
        clean_text
    )

    if address_match:

        address_value = address_match.group(1).strip()

        add_detection(
            "Address",
            address_value,
            box,
            "high"
        )


    # --------------------------------------------------------
    # DOB
    # --------------------------------------------------------

    dob_match = DOB_PATTERN.search(
        clean_text
    )

    if dob_match:

        date_text = dob_match.group(1).strip()

        date_match = re.search(
            PATTERNS["Date"],
            date_text
        )

        if date_match:

            add_detection(
                "DOB",
                date_match.group(0),
                box,
                "high"
            )


    # --------------------------------------------------------
    # BANK ACCOUNT - LABELLED
    # --------------------------------------------------------

    account_match = BANK_ACCOUNT_LABEL_PATTERN.search(
        clean_text
    )

    if account_match:

        add_detection(
            "Bank Account",
            account_match.group(1),
            box,
            "high"
        )


# ============================================================
# DOCUMENT-LEVEL CONTEXT
# ============================================================

all_text = " ".join(
    str(item.get("text", ""))
    for item in ocr_data
).upper()


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

is_pan_document = (
    "PERMANENT ACCOUNT NUMBER" in all_text
    or "PAN CARD" in all_text
    or "INCOME TAX DEPARTMENT" in all_text
)


is_aadhaar_document = (
    "AADHAAR" in all_text
    or "UNIQUE IDENTIFICATION" in all_text
    or "UIDAI" in all_text
)


is_bank_document = (
    "BANK" in all_text
    or "ACCOUNT NUMBER" in all_text
    or "ACCOUNT NO" in all_text
    or "IFSC" in all_text
)


# ============================================================
# CONTEXT CONFIDENCE BOOST
# ============================================================

if is_pan_document:

    for item in detected_items:

        if item["type"] == "PAN":

            item["confidence"] = "high"


if is_aadhaar_document:

    for item in detected_items:

        if item["type"] == "Aadhaar":

            item["confidence"] = "high"


if is_bank_document:

    for item in detected_items:

        if item["type"] in [
            "Bank Account",
            "IFSC"
        ]:

            item["confidence"] = "high"


# ============================================================
# REMOVE DUPLICATES
# ============================================================

unique_items = []
seen = set()


for item in detected_items:

    key = (
        item["type"],
        item["value"].lower(),
        tuple(item["box"])
    )

    if key in seen:
        continue

    seen.add(key)

    unique_items.append(item)


detected_items = unique_items


# ============================================================
# SORT DETECTIONS
# ============================================================

detected_items.sort(
    key=lambda item: (
        item["box"][1],
        item["box"][0]
    )
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print(
    "===== SENSITIVE INFORMATION DETECTED ====="
)

print()


if detected_items:

    for item in detected_items:

        print(
            f"Type: {item['type']}"
        )

        print(
            "Value: [REDACTED]"
        )

        print(
            f"Confidence: {item['confidence']}"
        )

        print(
            f"Box: {item['box']}"
        )

        print()

else:

    print(
        "No sensitive information detected."
    )


print(
    f"Total sensitive items: {len(detected_items)}"
)


# ============================================================
# SAVE RESULTS
# ============================================================

try:

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            detected_items,
            file,
            indent=4
        )

except Exception as error:

    print(
        "ERROR: Could not save detection results!"
    )

    print(error)

    exit(1)


print()

print(
    f"Detection results saved to: {OUTPUT_FILE}"
)

print(
    "Sensitive-data detection completed!"
)