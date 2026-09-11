import json
import re
from pathlib import Path

import cv2


# ============================================================
# QR RESULT HELPERS
# ============================================================

def _empty_result():
    return {
        "detected": False,
        "codes_detected": 0,
        "codes": [],
        "document_type": None,
        "identity_number": None,
        "name": None,
        "dob": None,
        "gender": None,
        "raw_payload": None,
    }


def _clean_text(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _normalize_pan(value):
    if value is None:
        return None

    value = re.sub(
        r"[^A-Z0-9]",
        "",
        str(value).upper(),
    )

    if re.fullmatch(
        r"[A-Z]{5}[0-9]{4}[A-Z]",
        value,
    ):
        return value

    return None


def _normalize_aadhaar(value):
    if value is None:
        return None

    digits = re.sub(
        r"\D",
        "",
        str(value),
    )

    if len(digits) == 12:
        return digits

    return None


def _normalize_gender(value):
    if value is None:
        return None

    value = str(value).strip().upper()

    aliases = {
        "M": "MALE",
        "MALE": "MALE",
        "F": "FEMALE",
        "FEMALE": "FEMALE",
        "T": "OTHER",
        "O": "OTHER",
        "OTHER": "OTHER",
    }

    return aliases.get(
        value,
        value if value else None,
    )


def _normalize_date(value):
    if value is None:
        return None

    text = str(value).strip()

    # Standard DD/MM/YYYY style.
    match = re.search(
        r"\b(\d{1,2})"
        r"[\/\-.]"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{4})\b",
        text,
    )

    if match:
        return (
            f"{int(match.group(1)):02d}/"
            f"{int(match.group(2)):02d}/"
            f"{int(match.group(3)):04d}"
        )

    # Compact YYYY-MM-DD / YYYY/MM/DD.
    match = re.search(
        r"\b(\d{4})"
        r"[\/\-.]"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{1,2})\b",
        text,
    )

    if match:
        return (
            f"{int(match.group(3)):02d}/"
            f"{int(match.group(2)):02d}/"
            f"{int(match.group(1)):04d}"
        )

    # Four-digit year, useful for Aadhaar Year of Birth.
    match = re.fullmatch(
        r"(19\d{2}|20\d{2})",
        text,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# PAYLOAD EXTRACTION
# ============================================================

def _extract_pan_number(text):
    if not text:
        return None

    match = re.search(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        str(text).upper(),
    )

    if match:
        return _normalize_pan(
            match.group(0)
        )

    return None


def _extract_aadhaar_number(text):
    if not text:
        return None

    # Look for grouped Aadhaar number.
    match = re.search(
        r"\b\d{4}"
        r"[\s\-]?\d{4}"
        r"[\s\-]?\d{4}\b",
        str(text),
    )

    if match:
        return _normalize_aadhaar(
            match.group(0)
        )

    return None


def _extract_name_from_text(text):
    if not text:
        return None

    value = str(text).strip()

    # Common key=value / key:value formats.
    patterns = [
        r"(?:name|full\s*name)\s*[:=]\s*"
        r"([A-Za-z][A-Za-z .'-]{2,})",

        r'"name"\s*:\s*'
        r'"([^"]+)"',

        r"'name'\s*:\s*"
        r"'([^']+)'",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            candidate = (
                match.group(1).strip()
            )

            if candidate:
                return candidate

    return None


def _extract_gender_from_text(text):
    if not text:
        return None

    value = str(text).strip()

    patterns = [
        r"(?:gender|sex)\s*[:=]\s*"
        r"(MALE|FEMALE|OTHER|M|F|T|O)\b",

        r'"gender"\s*:\s*'
        r'"([^"]+)"',

        r"'gender'\s*:\s*"
        r"'([^']+)'",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:
            return _normalize_gender(
                match.group(1)
            )

    return None


def _extract_dob_from_text(text):
    if not text:
        return None

    value = str(text).strip()

    patterns = [
        r"(?:dob|date\s*of\s*birth|"
        r"birth\s*date|year\s*of\s*birth)"
        r"\s*[:=]\s*"
        r"([0-9\/\-.]+)",

        r'"dob"\s*:\s*'
        r'"([^"]+)"',

        r'"dateOfBirth"\s*:\s*'
        r'"([^"]+)"',

        r"'dob'\s*:\s*"
        r"'([^']+)'",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            value,
            re.IGNORECASE,
        )

        if match:

            result = _normalize_date(
                match.group(1)
            )

            if result:
                return result

    return None


# ============================================================
# STRUCTURED PAYLOAD
# ============================================================

def _parse_json_payload(text):
    try:
        parsed = json.loads(
            text
        )

    except Exception:
        return None

    if not isinstance(
        parsed,
        dict,
    ):
        return None

    return parsed


def _find_nested_value(
    data,
    possible_keys,
):
    if isinstance(
        data,
        dict,
    ):

        for key, value in data.items():

            normalized_key = (
                str(key)
                .strip()
                .lower()
                .replace("_", "")
                .replace("-", "")
                .replace(" ", "")
            )

            normalized_keys = {
                str(candidate)
                .strip()
                .lower()
                .replace("_", "")
                .replace("-", "")
                .replace(" ", "")
                for candidate in possible_keys
            }

            if normalized_key in normalized_keys:
                return value

        for value in data.values():

            nested = _find_nested_value(
                value,
                possible_keys,
            )

            if nested is not None:
                return nested

    elif isinstance(
        data,
        list,
    ):

        for item in data:

            nested = _find_nested_value(
                item,
                possible_keys,
            )

            if nested is not None:
                return nested

    return None


def _parse_structured_payload(text):
    data = _parse_json_payload(
        text
    )

    if data is None:
        return {}

    result = {}

    result["pan_number"] = _normalize_pan(
        _find_nested_value(
            data,
            [
                "pan",
                "pan_number",
                "panNumber",
                "permanentAccountNumber",
            ],
        )
    )

    result["aadhaar_number"] = (
        _normalize_aadhaar(
            _find_nested_value(
                data,
                [
                    "aadhaar",
                    "aadhaar_number",
                    "aadhaarNumber",
                    "uid",
                    "uidNumber",
                ],
            )
        )
    )

    name = _find_nested_value(
        data,
        [
            "name",
            "full_name",
            "fullName",
            "applicantName",
            "holderName",
        ],
    )

    if name:
        result["name"] = _clean_text(
            name
        )

    gender = _find_nested_value(
        data,
        [
            "gender",
            "sex",
        ],
    )

    if gender:
        result["gender"] = (
            _normalize_gender(
                gender
            )
        )

    dob = _find_nested_value(
        data,
        [
            "dob",
            "date_of_birth",
            "dateOfBirth",
            "birthDate",
            "yearOfBirth",
        ],
    )

    if dob:
        result["dob"] = (
            _normalize_date(
                dob
            )
        )

    return result


# ============================================================
# PAYLOAD CLASSIFICATION
# ============================================================

def _classify_payload(text):
    """
    Classify a decoded QR payload as PAN, Aadhaar, or UNKNOWN.

    The decoder intentionally does not depend on one fixed QR
    payload format. It looks for recognized identity patterns
    and common field labels.
    """

    if not text:
        return {
            "document_type": None,
            "identity_number": None,
            "name": None,
            "dob": None,
            "gender": None,
        }

    payload = str(text).strip()

    structured = _parse_structured_payload(
        payload
    )

    pan_number = (
        structured.get("pan_number")
        or _extract_pan_number(
            payload
        )
    )

    aadhaar_number = (
        structured.get("aadhaar_number")
        or _extract_aadhaar_number(
            payload
        )
    )

    name = (
        structured.get("name")
        or _extract_name_from_text(
            payload
        )
    )

    dob = (
        structured.get("dob")
        or _extract_dob_from_text(
            payload
        )
    )

    gender = (
        structured.get("gender")
        or _extract_gender_from_text(
            payload
        )
    )

    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    if pan_number:

        return {
            "document_type": "PAN",
            "identity_number": pan_number,
            "name": name,
            "dob": dob,
            "gender": gender,
        }

    # --------------------------------------------------------
    # Aadhaar
    # --------------------------------------------------------

    if aadhaar_number:

        return {
            "document_type": "AADHAAR",
            "identity_number": aadhaar_number,
            "name": name,
            "dob": dob,
            "gender": gender,
        }

    # --------------------------------------------------------
    # Aadhaar secure QR may not expose the number as simple
    # plaintext. In that situation, retain the raw payload and
    # mark it as an Aadhaar candidate only when recognizable
    # Aadhaar-specific labels are present.
    # --------------------------------------------------------

    upper_payload = payload.upper()

    aadhaar_markers = [
        "AADHAAR",
        "AADHAR",
        "UIDAI",
        "UNIQUE IDENTIFICATION",
    ]

    if any(
        marker in upper_payload
        for marker in aadhaar_markers
    ):

        return {
            "document_type": "AADHAAR",
            "identity_number": None,
            "name": name,
            "dob": dob,
            "gender": gender,
        }

    return {
        "document_type": None,
        "identity_number": None,
        "name": name,
        "dob": dob,
        "gender": gender,
    }


# ============================================================
# SINGLE CODE DECODING
# ============================================================

def _decode_with_detector(
    image,
):
    detector = cv2.QRCodeDetector()

    decoded_items = []

    # --------------------------------------------------------
    # Multiple QR codes.
    # --------------------------------------------------------

    try:

        result = (
            detector.detectAndDecodeMulti(
                image
            )
        )

        if len(result) == 4:

            found, decoded_info, points, _ = (
                result
            )

            if found and decoded_info:

                for index, payload in enumerate(
                    decoded_info
                ):

                    if payload is None:
                        continue

                    payload = str(
                        payload
                    ).strip()

                    if not payload:
                        continue

                    decoded_items.append(
                        {
                            "payload": payload,
                            "points": (
                                points[index].tolist()
                                if (
                                    points is not None
                                    and index < len(points)
                                )
                                else None
                            ),
                        }
                    )

    except Exception:
        pass

    # --------------------------------------------------------
    # Single QR fallback.
    # --------------------------------------------------------

    if not decoded_items:

        try:

            payload, points, _ = (
                detector.detectAndDecode(
                    image
                )
            )

            if payload:

                decoded_items.append(
                    {
                        "payload": str(
                            payload
                        ).strip(),
                        "points": (
                            points.tolist()
                            if points is not None
                            else None
                        ),
                    }
                )

        except Exception:
            pass

    return decoded_items


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def _candidate_images(image):
    """
    Generate a small set of practical QR-reading variants.

    This improves robustness for phone photos and scanned cards
    without changing the user's stored image.
    """

    candidates = [
        image
    ]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    candidates.append(
        gray
    )

    scaled = cv2.resize(
        gray,
        None,
        fx=1.5,
        fy=1.5,
        interpolation=cv2.INTER_CUBIC,
    )

    candidates.append(
        scaled
    )

    thresholded = cv2.adaptiveThreshold(
        scaled,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )

    candidates.append(
        thresholded
    )

    return candidates


# ============================================================
# PUBLIC API
# ============================================================

def scan_qr(
    image_path: str,
):
    """
    Scan QR codes from a document image.

    Supports both PAN and Aadhaar QR use cases.

    Returns decoded payloads plus best-effort extraction of:

        document_type
        identity_number
        name
        dob
        gender

    QR decoding failure is not treated as fraud.
    """

    result = _empty_result()

    path = Path(
        image_path
    )

    if not path.exists():
        result["error"] = (
            "QR source image not found."
        )
        return result

    image = cv2.imread(
        str(path)
    )

    if image is None:
        result["error"] = (
            "Unable to read image for QR scanning."
        )
        return result

    all_decoded = []

    for candidate_image in _candidate_images(
        image
    ):

        decoded = _decode_with_detector(
            candidate_image
        )

        for item in decoded:

            payload = item.get(
                "payload"
            )

            # Avoid duplicates.
            if any(
                existing.get(
                    "payload"
                ) == payload
                for existing in all_decoded
            ):
                continue

            all_decoded.append(
                item
            )

    result["codes_detected"] = len(
        all_decoded
    )

    result["detected"] = bool(
        all_decoded
    )

    if not all_decoded:
        return result

    result["codes"] = []

    # Best candidate is the first recognizable PAN/Aadhaar code.
    best_classification = None

    for item in all_decoded:

        payload = item.get(
            "payload"
        )

        classification = _classify_payload(
            payload
        )

        code_result = {
            "payload": payload,
            "points": item.get(
                "points"
            ),
            "document_type": (
                classification[
                    "document_type"
                ]
            ),
            "identity_number": (
                classification[
                    "identity_number"
                ]
            ),
            "name": (
                classification[
                    "name"
                ]
            ),
            "dob": (
                classification[
                    "dob"
                ]
            ),
            "gender": (
                classification[
                    "gender"
                ]
            ),
        }

        result["codes"].append(
            code_result
        )

        if (
            best_classification is None
            and classification[
                "document_type"
            ] is not None
        ):

            best_classification = (
                classification
            )

            result["raw_payload"] = (
                payload
            )

    # If no classified code exists, still preserve the first
    # decoded payload for diagnostics/future format support.
    if best_classification is None:

        first = result["codes"][0]

        result["raw_payload"] = (
            first.get("payload")
        )

        return result

    result["document_type"] = (
        best_classification[
            "document_type"
        ]
    )

    result["identity_number"] = (
        best_classification[
            "identity_number"
        ]
    )

    result["name"] = (
        best_classification[
            "name"
        ]
    )

    result["dob"] = (
        best_classification[
            "dob"
        ]
    )

    result["gender"] = (
        best_classification[
            "gender"
        ]
    )

    return result


def scan_document_qr(
    image_path: str,
):
    """
    Alias kept for convenient integration from the screening
    service.
    """

    return scan_qr(
        image_path
    )