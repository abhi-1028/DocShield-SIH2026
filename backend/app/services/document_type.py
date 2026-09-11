import re


# ============================================================
# DOCUMENT TYPES
# ============================================================

PAN = "PAN"
AADHAAR = "AADHAAR"
UNKNOWN = "UNKNOWN"


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_ocr_text(text: str) -> str:
    """
    Normalize OCR text for document-type detection.
    """

    if not text:
        return ""

    text = str(text).upper()

    # Normalize common OCR separators
    text = text.replace("|", " ")
    text = text.replace("_", " ")

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# PAN DETECTION
# ============================================================

def detect_pan(text: str) -> int:
    """
    Return a confidence-like score for PAN detection.

    Higher score = stronger PAN evidence.
    """

    score = 0

    normalized = normalize_ocr_text(text)

    # --------------------------------------------------------
    # PAN-related keywords
    # --------------------------------------------------------

    pan_keywords = [
        "PERMANENT ACCOUNT NUMBER",
        "PERMANENT ACCOUNT",
        "PAN CARD",
        "PAN",
        "INCOME TAX",
    ]

    for keyword in pan_keywords:

        if keyword in normalized:
            score += 3

    # --------------------------------------------------------
    # PAN number pattern
    #
    # Standard PAN format:
    # ABCDE1234F
    # --------------------------------------------------------

    pan_pattern = re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    )

    if pan_pattern.search(normalized):
        score += 6

    return score


# ============================================================
# AADHAAR DETECTION
# ============================================================

def detect_aadhaar(text: str) -> int:
    """
    Return a confidence-like score for Aadhaar detection.

    Higher score = stronger Aadhaar evidence.
    """

    score = 0

    normalized = normalize_ocr_text(text)

    # --------------------------------------------------------
    # Aadhaar-related keywords
    # --------------------------------------------------------

    aadhaar_keywords = [
        "AADHAAR",
        "AADHAR",
        "UNIQUE IDENTIFICATION",
        "UNIQUE IDENTIFICATION AUTHORITY",
        "UIDAI",
    ]

    for keyword in aadhaar_keywords:

        if keyword in normalized:
            score += 3

    # --------------------------------------------------------
    # Aadhaar number detection
    #
    # Handles:
    # 123456789012
    # 1234 5678 9012
    # 1234-5678-9012
    # --------------------------------------------------------

    compact_text = re.sub(
        r"[\s\-]",
        "",
        normalized
    )

    aadhaar_pattern = re.compile(
        r"\b\d{12}\b"
    )

    if aadhaar_pattern.search(compact_text):
        score += 6

    # Also detect three groups of four digits.
    grouped_pattern = re.compile(
        r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b"
    )

    if grouped_pattern.search(normalized):
        score += 6

    return score


# ============================================================
# MAIN DOCUMENT TYPE DETECTOR
# ============================================================

def detect_document_type(text: str) -> dict:
    """
    Detect the likely document type from OCR text.

    Returns:
        {
            "document_type": "PAN" | "AADHAAR" | "UNKNOWN",
            "confidence": float,
            "pan_score": int,
            "aadhaar_score": int
        }

    This is a screening-level classifier.
    It is NOT proof of document authenticity.
    """

    pan_score = detect_pan(text)

    aadhaar_score = detect_aadhaar(text)

    # --------------------------------------------------------
    # No meaningful evidence
    # --------------------------------------------------------

    if pan_score == 0 and aadhaar_score == 0:

        return {
            "document_type": UNKNOWN,
            "confidence": 0.0,
            "pan_score": pan_score,
            "aadhaar_score": aadhaar_score,
        }

    # --------------------------------------------------------
    # PAN wins
    # --------------------------------------------------------

    if pan_score > aadhaar_score:

        confidence = min(
            100.0,
            (pan_score / 9.0) * 100.0
        )

        return {
            "document_type": PAN,
            "confidence": round(
                confidence,
                2
            ),
            "pan_score": pan_score,
            "aadhaar_score": aadhaar_score,
        }

    # --------------------------------------------------------
    # Aadhaar wins
    # --------------------------------------------------------

    if aadhaar_score > pan_score:

        confidence = min(
            100.0,
            (aadhaar_score / 9.0) * 100.0
        )

        return {
            "document_type": AADHAAR,
            "confidence": round(
                confidence,
                2
            ),
            "pan_score": pan_score,
            "aadhaar_score": aadhaar_score,
        }

    # --------------------------------------------------------
    # Equal evidence
    # --------------------------------------------------------

    return {
        "document_type": UNKNOWN,
        "confidence": 0.0,
        "pan_score": pan_score,
        "aadhaar_score": aadhaar_score,
    }