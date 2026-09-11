import re
from datetime import datetime


# ============================================================
# DOCUMENT TYPES
# ============================================================

PAN = "PAN"
AADHAAR = "AADHAAR"
UNKNOWN = "UNKNOWN"


# ============================================================
# LINE NORMALIZATION
# ============================================================

def normalize_lines(ocr_text: str) -> list[str]:
    """
    Convert OCR output into clean, non-empty lines.
    """

    lines = []

    if not ocr_text:
        return lines

    for line in str(ocr_text).splitlines():

        line = re.sub(
            r"\s+",
            " ",
            line,
        ).strip()

        if line:
            lines.append(line)

    return lines


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_name(value: str | None):
    """
    Clean a person name while preserving useful punctuation.
    """

    if value is None:
        return None

    value = str(value).strip()

    value = re.sub(
        r":\s*$",
        "",
        value,
    ).strip()

    value = re.sub(
        r"[^A-Za-z .'-]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value if value else None


def normalize_name(value: str | None):
    """
    Normalize names for comparison.
    """

    if value is None:
        return None

    value = clean_name(value)

    if not value:
        return None

    value = value.upper()

    value = re.sub(
        r"[-]+",
        " ",
        value,
    )

    value = re.sub(
        r"[^A-Z ]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value if value else None


def normalize_id(value: str | None):
    """
    Normalize identity/document numbers.

    Identity numbers remain strictly comparable.
    """

    if value is None:
        return None

    value = str(value).upper()

    return re.sub(
        r"[^A-Z0-9]",
        "",
        value,
    ) or None


def _format_valid_date(
    day: int,
    month: int,
    year: int,
):
    """
    Validate and format a date.
    """

    try:
        datetime(
            year,
            month,
            day,
        )
    except ValueError:
        return None

    return (
        f"{day:02d}/"
        f"{month:02d}/"
        f"{year:04d}"
    )


def _extract_date_from_text(
    value: str,
):
    """
    Extract a date from OCR text.

    Handles normal formats such as:

        14/05/1995
        14-05-1995
        14.05.1995
        1/2/1990

    Also handles conservative OCR corruption such as:

        22803/2001

    where one extra OCR digit has appeared before the month/year
    separator. The function only accepts a correction when it
    produces a valid calendar date.
    """

    if not value:
        return None

    text = str(value).strip()

    # --------------------------------------------------------
    # Standard date.
    # --------------------------------------------------------

    normal_match = re.search(
        r"\b(\d{1,2})"
        r"[\/\-.]"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{4})\b",
        text,
    )

    if normal_match:

        formatted = _format_valid_date(
            int(normal_match.group(1)),
            int(normal_match.group(2)),
            int(normal_match.group(3)),
        )

        if formatted:
            return formatted

    # --------------------------------------------------------
    # Compact OCR date.
    #
    # Example:
    #
    # 2203/2001
    #
    # means:
    #
    # 22/03/2001
    # --------------------------------------------------------

    compact_match = re.search(
        r"\b(\d{3,5})"
        r"[\/\-.]"
        r"(\d{4})\b",
        text,
    )

    if not compact_match:
        return None

    compact_digits = compact_match.group(
        1
    )

    year = int(
        compact_match.group(2)
    )

    # --------------------------------------------------------
    # Four digits:
    #
    # DDMM
    # --------------------------------------------------------

    if len(compact_digits) == 4:

        formatted = _format_valid_date(
            int(compact_digits[:2]),
            int(compact_digits[2:]),
            year,
        )

        if formatted:
            return formatted

    # --------------------------------------------------------
    # Three digits:
    #
    # DMM
    # --------------------------------------------------------

    if len(compact_digits) == 3:

        formatted = _format_valid_date(
            int(compact_digits[:1]),
            int(compact_digits[1:]),
            year,
        )

        if formatted:
            return formatted

    # --------------------------------------------------------
    # Five digits:
    #
    # Example:
    #
    # 22803/2001
    #
    # Try removing one digit and accept only valid dates.
    # --------------------------------------------------------

    if len(compact_digits) == 5:

        valid_candidates = []

        for remove_index in range(
            len(compact_digits)
        ):

            candidate_digits = (
                compact_digits[:remove_index]
                + compact_digits[
                    remove_index + 1:
                ]
            )

            if len(candidate_digits) != 4:
                continue

            day = int(
                candidate_digits[:2]
            )

            month = int(
                candidate_digits[2:]
            )

            formatted = _format_valid_date(
                day,
                month,
                year,
            )

            if formatted:

                valid_candidates.append(
                    (
                        remove_index,
                        formatted,
                    )
                )

        # Prefer removing an interior digit.
        if valid_candidates:

            interior = [
                candidate
                for candidate in valid_candidates
                if (
                    candidate[0] > 0
                    and candidate[0]
                    < len(compact_digits) - 1
                )
            ]

            if interior:
                return interior[0][1]

            return valid_candidates[0][1]

    return None


def _extract_year_of_birth(
    value: str,
):
    """
    Extract an explicit four-digit year of birth.

    Aadhaar documents commonly contain:

        Year of Birth : 1992

    This is intentionally only used when the OCR text explicitly
    represents a year-of-birth field.
    """

    if not value:
        return None

    match = re.search(
        r"\b(19\d{2}|20\d{2})\b",
        str(value),
    )

    if not match:
        return None

    year = int(
        match.group(1)
    )

    # Conservative sanity range for a birth year.
    current_year = datetime.now().year

    if 1900 <= year <= current_year:
        return str(year)

    return None


def normalize_date(value: str | None):
    """
    Normalize common date formats to DD/MM/YYYY.

    Also accepts a four-digit year such as:

        1992

    which is used for Aadhaar Year of Birth fields.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    extracted = _extract_date_from_text(
        value
    )

    if extracted:
        return extracted

    # --------------------------------------------------------
    # Explicit four-digit year.
    #
    # This supports Aadhaar:
    #
    # Year of Birth : 1992
    # --------------------------------------------------------

    year_only = re.fullmatch(
        r"(19\d{2}|20\d{2})",
        value,
    )

    if year_only:

        year = int(
            year_only.group(1)
        )

        current_year = datetime.now().year

        if 1900 <= year <= current_year:
            return str(year)

    normalized = re.sub(
        r"[.\-]",
        "/",
        value,
    )

    normalized = re.sub(
        r"\s*/\s*",
        "/",
        normalized,
    )

    match = re.search(
        r"\b(\d{1,2})/"
        r"(\d{1,2})/"
        r"(\d{4})\b",
        normalized,
    )

    if not match:
        return normalize_value(
            value
        )

    formatted = _format_valid_date(
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
    )

    return (
        formatted
        or normalize_value(value)
    )


def normalize_gender(value: str | None):
    """
    Normalize gender values.
    """

    if value is None:
        return None

    value = str(value).strip().upper()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    aliases = {
        "M": "MALE",
        "MALE": "MALE",
        "F": "FEMALE",
        "FEMALE": "FEMALE",
        "O": "OTHER",
        "OTHER": "OTHER",
    }

    return aliases.get(
        value,
        value if value else None,
    )


def normalize_value(value: str | None):
    """
    General-purpose normalization.
    """

    if value is None:
        return None

    value = str(value).strip().upper()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value if value else None


# ============================================================
# FIELD-SPECIFIC NORMALIZATION
# ============================================================

def normalize_field_value(
    field: str,
    value,
):
    """
    Apply the correct normalization strategy for a field.
    """

    if value is None:
        return None

    if field in {
        "id_number",
        "pan_number",
        "aadhaar_number",
    }:

        return normalize_id(
            value
        )

    if field in {
        "name",
        "father_name",
    }:

        return normalize_name(
            value
        )

    if field == "dob":

        return normalize_date(
            value
        )

    if field == "gender":

        return normalize_gender(
            value
        )

    return normalize_value(
        value
    )


# ============================================================
# FIELD LABELS
# ============================================================

def is_field_label(
    line: str,
) -> bool:

    if not line:
        return False

    normalized = re.sub(
        r"[^A-Z0-9 ]",
        "",
        line.upper(),
    ).strip()

    known_labels = {
        "FULL NAME",
        "NAME",
        "NANEI",
        "NAV",
        "NAAV",

        "DATE",
        "OF BIRTH",
        "DATE OF BIRTH",
        "DOB",
        "D O B",
        "DOB OF BIRTH",

        "YEAR OF BIRTH",
        "YEAR BIRTH",
        "YOB",

        "PHOTO",

        "ID NUMBER",
        "ID NO",
        "IDENTIFICATION NO",
        "DOCUMENT NO",

        "AADHAAR",
        "AADHAR",
        "AADHAAR NO",
        "AADHAAR NUMBER",
        "AADHAR NO",
        "AADHAR NUMBER",

        "GENDER",

        "REFERENCE ID",
        "ADDRESS",

        "PERMANENT ACCOUNT NUMBER",
        "PERMANENT ACCOUNT NUMBER CARD",

        "PAN",
        "PAN NO",
        "PAN NUMBER",

        "FATHER NAME",
        "FATHERS NAME",
        "FATHER'S NAME",
        "FATHER",
    }

    return normalized in known_labels


# ============================================================
# LABEL HELPERS
# ============================================================

def _normalize_label_text(
    value: str,
):
    if value is None:
        return ""

    value = str(value).upper().strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def _extract_labeled_value(
    line: str,
    labels: list[str],
):
    """
    Extract a value after a known label.

    Supports forms such as:

        NAME: VALUE
        NAME / NAV: VALUE
        GENDER / LING: FEMALE
    """

    if not line:
        return None

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    pattern = (
        r"^\s*(?:"
        + label_pattern
        + r")"
        r"(?:\s*/\s*[^:;\-]+)?"
        r"\s*[:\-]\s*"
        r"(.+?)\s*$"
    )

    match = re.search(
        pattern,
        line,
        re.IGNORECASE,
    )

    if not match:
        return None

    value = match.group(
        1
    ).strip()

    return value if value else None


def _line_contains_label(
    line: str,
    labels: list[str],
):
    if not line:
        return False

    upper = _normalize_label_text(
        line
    )

    for label in labels:

        if re.search(
            rf"\b{re.escape(label)}\b",
            upper,
        ):
            return True

    return False


def _looks_like_label_fragment(
    value: str | None,
):
    """
    Detect OCR fragments that are likely labels rather than
    actual values.
    """

    if value is None:
        return True

    cleaned = str(value).strip()

    if not cleaned:
        return True

    if cleaned.endswith(":"):
        return True

    normalized = re.sub(
        r"[^A-Z0-9 ]",
        "",
        cleaned.upper(),
    ).strip()

    label_fragments = {
        "NAME",
        "FULL NAME",
        "NANEI",
        "NAV",
        "NAAV",
        "GENDER",
        "DOB",
        "DATE",
        "DATE OF BIRTH",
        "DOB OF BIRTH",
        "YEAR OF BIRTH",
        "YEAR BIRTH",
        "YOB",
        "FATHER",
        "FATHER NAME",
        "FATHERS NAME",
        "FATHER S NAME",
        "ADDRESS",
        "PHOTO",
        "AADHAAR",
        "AADHAAR NO",
        "AADHAAR NUMBER",
        "AADHAR",
        "AADHAR NO",
        "AADHAR NUMBER",
    }

    return normalized in label_fragments


def _looks_like_aadhaar_name(
    value: str | None,
):
    """
    Determine whether an OCR line is a plausible English name
    from an Aadhaar document.

    The helper intentionally rejects common metadata/address
    lines.
    """

    if value is None:
        return False

    cleaned = clean_name(
        value
    )

    if not cleaned:
        return False

    upper = cleaned.upper()

    if _looks_like_label_fragment(
        cleaned
    ):
        return False

    blocked_words = {
        "GOVERNMENT",
        "INDIA",
        "AUTHORITY",
        "UNIQUE",
        "IDENTIFICATION",
        "ENROLLMENT",
        "ADDRESS",
        "RESIDENCY",
        "ROAD",
        "PARK",
        "BHOPAL",
        "MADHYA",
        "PRADESH",
        "MALE",
        "FEMALE",
        "YEAR",
        "BIRTH",
        "AADHAAR",
    }

    words = upper.split()

    if any(
        word in blocked_words
        for word in words
    ):
        return False

    # Avoid lines containing obvious address/reference text.
    if re.search(
        r"\b(S/O|D/O|W/O|C/O|NO\.?|PIN|ENROLLMENT)\b",
        upper,
    ):
        return False

    # A simple English-person-name heuristic.
    if not re.fullmatch(
        r"[A-Za-z]+(?:[ .'-][A-Za-z]+)+",
        cleaned,
    ):
        return False

    return True


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

def detect_document_type(
    lines: list[str],
):

    text = " ".join(
        lines
    ).upper()

    pan_pattern = (
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    )

    has_pan_number = (
        re.search(
            pan_pattern,
            text,
        )
        is not None
    )

    has_pan_keyword = (
        "PERMANENT ACCOUNT NUMBER"
        in text
        or re.search(
            r"\bPAN\b",
            text,
        )
        is not None
    )

    if (
        has_pan_number
        or has_pan_keyword
    ):
        return PAN

    if (
        "AADHAAR" in text
        or "AADHAR" in text
        or "UNIQUE IDENTIFICATION AUTHORITY"
        in text
    ):
        return AADHAAR

    return UNKNOWN


# ============================================================
# DATE / YEAR OF BIRTH EXTRACTION
# ============================================================

def extract_dob(
    lines: list[str],
):

    for i, line in enumerate(lines):

        upper = line.upper()

        # ----------------------------------------------------
        # Normal DOB labels.
        # ----------------------------------------------------

        label_date_match = re.search(
            r"(?:DATE\s+OF\s+BIRTH|"
            r"DOB\s+OF\s+BIRTH|"
            r"DOB|"
            r"D\.O\.B)"
            r"(?:\s*/\s*[^:;\-]+)?"
            r"\s*[:\-]?\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if label_date_match:

            extracted = (
                _extract_date_from_text(
                    label_date_match.group(1)
                )
            )

            if extracted:
                return extracted

        # ----------------------------------------------------
        # Aadhaar Year of Birth.
        #
        # Example:
        #
        # Year of Birth : 1992
        # ----------------------------------------------------

        yob_match = re.search(
            r"(?:YEAR\s+OF\s+BIRTH|"
            r"YEAR\s+BIRTH|"
            r"YOB)"
            r"(?:\s*/\s*[^:;\-]+)?"
            r"\s*[:\-]?\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if yob_match:

            year = _extract_year_of_birth(
                yob_match.group(1)
            )

            if year:
                return year

        # ----------------------------------------------------
        # Label detection with nearby line.
        # ----------------------------------------------------

        has_dob_label = (
            "DATE OF BIRTH" in upper
            or "DOB OF BIRTH" in upper
            or re.search(
                r"\bDOB\b",
                upper,
            )
            is not None
            or "D.O.B" in upper
        )

        has_yob_label = (
            "YEAR OF BIRTH" in upper
            or "YEAR BIRTH" in upper
            or re.search(
                r"\bYOB\b",
                upper,
            )
            is not None
        )

        if (
            has_dob_label
            or has_yob_label
        ):

            extracted = (
                _extract_date_from_text(
                    line
                )
            )

            if extracted:
                return extracted

            if has_yob_label:

                year = _extract_year_of_birth(
                    line
                )

                if year:
                    return year

            # ------------------------------------------------
            # Date/year on nearby line.
            # ------------------------------------------------

            for offset in (
                1,
                2,
            ):

                if (
                    i + offset
                    >= len(lines)
                ):
                    break

                candidate = lines[
                    i + offset
                ]

                extracted = (
                    _extract_date_from_text(
                        candidate
                    )
                )

                if extracted:
                    return extracted

                if has_yob_label:

                    year = _extract_year_of_birth(
                        candidate
                    )

                    if year:
                        return year

    return None


# ============================================================
# GENDER
# ============================================================

def extract_gender(
    lines: list[str],
):

    gender_labels = [
        "GENDER",
    ]

    for i, line in enumerate(lines):

        if _line_contains_label(
            line,
            gender_labels,
        ):

            match = re.search(
                r"\b(MALE|FEMALE|OTHER)\b",
                line,
                re.IGNORECASE,
            )

            if match:

                return normalize_gender(
                    match.group(1)
                )

            if (
                i + 1
                < len(lines)
            ):

                candidate = (
                    lines[
                        i + 1
                    ]
                    .strip()
                    .upper()
                )

                match = re.search(
                    r"\b(MALE|FEMALE|OTHER)\b",
                    candidate,
                    re.IGNORECASE,
                )

                if match:

                    return normalize_gender(
                        match.group(1)
                    )

        match = re.search(
            r"\b(MALE|FEMALE|OTHER)\b",
            line.upper(),
        )

        if match:

            return normalize_gender(
                match.group(1)
            )

    return None


# ============================================================
# PAN NUMBER
# ============================================================

def extract_pan_number(
    lines: list[str],
):

    pan_pattern = (
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    )

    for line in lines:

        matches = re.findall(
            pan_pattern,
            line.upper(),
        )

        if matches:
            return matches[0]

    return None


# ============================================================
# AADHAAR NUMBER
# ============================================================

def extract_aadhaar_number(
    lines: list[str],
):

    aadhaar_pattern = (
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
    )

    for line in lines:

        matches = re.findall(
            aadhaar_pattern,
            line,
        )

        for match in matches:

            digits = re.sub(
                r"\D",
                "",
                match,
            )

            if len(digits) == 12:
                return digits

    # --------------------------------------------------------
    # Handle OCR splitting a 12-digit Aadhaar number across
    # adjacent lines.
    # --------------------------------------------------------

    for i in range(
        len(lines)
    ):

        combined = lines[i]

        if (
            i + 1
            < len(lines)
        ):

            combined += (
                " "
                + lines[
                    i + 1
                ]
            )

        digits = re.sub(
            r"\D",
            "",
            combined,
        )

        if len(digits) == 12:

            if (
                len(
                    re.findall(
                        r"\d",
                        combined,
                    )
                )
                >= 12
            ):
                return digits

    # --------------------------------------------------------
    # Fallback for OCR that inserts spaces between individual
    # digit groups in a noisy way.
    # --------------------------------------------------------

    for i in range(
        len(lines)
    ):

        candidate = lines[i]

        digit_count = len(
            re.findall(
                r"\d",
                candidate,
            )
        )

        if digit_count == 12:

            cleaned = re.sub(
                r"\D",
                "",
                candidate,
            )

            if len(cleaned) == 12:
                return cleaned

    return None


# ============================================================
# GENERIC ID NUMBER
# ============================================================

def extract_id_number(
    lines: list[str],
):

    pan_number = extract_pan_number(
        lines
    )

    if pan_number:
        return pan_number

    aadhaar_number = (
        extract_aadhaar_number(
            lines
        )
    )

    if aadhaar_number:
        return aadhaar_number

    id_labels = {
        "ID NUMBER",
        "ID NO",
        "IDENTIFICATION NO",
        "DOCUMENT NO",
        "AADHAAR NO",
        "AADHAAR NUMBER",
        "AADHAR NO",
        "AADHAR NUMBER",
        "PAN NO",
        "PAN NUMBER",
    }

    for i, line in enumerate(lines):

        upper = (
            line.upper()
            .strip()
        )

        match = re.search(
            r"(?:ID\s+NUMBER|"
            r"ID\s+NO|"
            r"IDENTIFICATION\s+NO|"
            r"DOCUMENT\s+NO|"
            r"AADHAAR\s+NO|"
            r"AADHAAR\s+NUMBER|"
            r"AADHAR\s+NO|"
            r"AADHAR\s+NUMBER|"
            r"PAN\s+NO|"
            r"PAN\s+NUMBER)"
            r"(?:\s*/\s*[^:;\-]+)?"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9\- ]{3,})",
            line,
            re.IGNORECASE,
        )

        if match:

            candidate = (
                match.group(1)
                .upper()
                .strip()
            )

            return candidate

        if upper in id_labels:

            if (
                i + 1
                < len(lines)
            ):

                candidate = (
                    lines[
                        i + 1
                    ]
                    .strip()
                )

                if is_field_label(
                    candidate
                ):
                    continue

                cleaned = re.sub(
                    r"[^A-Z0-9\-]",
                    "",
                    candidate.upper(),
                )

                if len(cleaned) >= 4:
                    return cleaned

    return None


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(
    lines: list[str],
):

    name_labels = [
        "FULL NAME",
        "NAME",
    ]

    # --------------------------------------------------------
    # Explicit same-line field.
    # --------------------------------------------------------

    for line in lines:

        labeled_value = (
            _extract_labeled_value(
                line,
                name_labels,
            )
        )

        if labeled_value:

            cleaned = clean_name(
                labeled_value
            )

            if (
                cleaned
                and not _looks_like_label_fragment(
                    labeled_value
                )
            ):
                return cleaned

    # --------------------------------------------------------
    # Separate-line field.
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        if not _line_contains_label(
            line,
            name_labels,
        ):
            continue

        if re.search(
            r"\b(DOB|GENDER|ADDRESS|PHOTO|FATHER)\b",
            line.upper(),
        ):
            continue

        for candidate in lines[
            i + 1:i + 5
        ]:

            candidate_upper = (
                candidate
                .upper()
                .strip()
            )

            if _looks_like_label_fragment(
                candidate
            ):
                continue

            if is_field_label(
                candidate
            ):
                continue

            if re.search(
                r"\b(DOB|GENDER|ADDRESS|PHOTO|FATHER)\b",
                candidate_upper,
            ):
                break

            if _extract_date_from_text(
                candidate
            ):
                break

            if _extract_year_of_birth(
                candidate
            ):
                break

            if re.search(
                r"\b[A-Z]{5}\d{4}[A-Z]\b",
                candidate_upper,
            ):
                break

            candidate_digits = re.sub(
                r"\D",
                "",
                candidate,
            )

            if len(candidate_digits) == 12:
                break

            cleaned = clean_name(
                candidate
            )

            if not cleaned:
                continue

            if (
                cleaned.upper()
                in {
                    "NAME",
                    "FULL NAME",
                    "GENDER",
                    "DATE",
                    "DATE OF BIRTH",
                    "DOB",
                    "DOB OF BIRTH",
                    "YEAR OF BIRTH",
                    "YEAR BIRTH",
                    "YOB",
                    "NANEI",
                    "NAV",
                    "NAAV",
                }
            ):
                continue

            if not re.search(
                r"[A-Za-z]",
                cleaned,
            ):
                continue

            return cleaned

    # --------------------------------------------------------
    # PAN fallback.
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        upper = (
            line.upper()
            .strip()
        )

        if (
            "FATHER" in upper
            and i > 0
        ):

            previous = clean_name(
                lines[
                    i - 1
                ]
            )

            if (
                previous
                and len(previous) >= 3
                and not _looks_like_label_fragment(
                    previous
                )
            ):
                return previous

    return None


# ============================================================
# AADHAAR NAME EXTRACTION
# ============================================================

def extract_aadhaar_name(
    lines: list[str],
):
    """
    Extract English name from common Aadhaar layouts where the
    name does not have an explicit "NAME:" label.

    Example layout:

        To
        [Hindi name]
        Melvin Cherian
        S/O: Cherian Mg
        ...

    The function uses the "To" marker as a local anchor and then
    looks for the first plausible English person-name line.
    """

    for i, line in enumerate(lines):

        upper = line.upper().strip()

        if upper not in {
            "TO",
            "TO:",
        }:
            continue

        for candidate in lines[
            i + 1:i + 5
        ]:

            if _looks_like_aadhaar_name(
                candidate
            ):
                return clean_name(
                    candidate
                )

    # --------------------------------------------------------
    # Fallback for the lower Aadhaar card section.
    #
    # Look for a plausible English name immediately before
    # Year of Birth / Gender information.
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        candidate = clean_name(
            line
        )

        if not _looks_like_aadhaar_name(
            candidate
        ):
            continue

        nearby_text = " ".join(
            lines[i + 1:i + 4]
        ).upper()

        if (
            "YEAR OF BIRTH" in nearby_text
            or "YEAR BIRTH" in nearby_text
            or re.search(
                r"\bYOB\b",
                nearby_text,
            )
            or re.search(
                r"\b(MALE|FEMALE|OTHER)\b",
                nearby_text,
            )
        ):
            return candidate

    return None


# ============================================================
# FATHER NAME — PAN
# ============================================================

def extract_father_name(
    lines: list[str],
):

    father_labels = [
        "FATHER NAME",
        "FATHERS NAME",
        "FATHER'S NAME",
        "FATHER",
    ]

    # --------------------------------------------------------
    # Same-line.
    # --------------------------------------------------------

    for line in lines:

        labeled_value = (
            _extract_labeled_value(
                line,
                father_labels,
            )
        )

        if labeled_value:

            cleaned = clean_name(
                labeled_value
            )

            if (
                cleaned
                and not _looks_like_label_fragment(
                    labeled_value
                )
            ):
                return cleaned

    # --------------------------------------------------------
    # Separate-line.
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        if not _line_contains_label(
            line,
            father_labels,
        ):
            continue

        if (
            i + 1
            >= len(lines)
        ):
            continue

        candidate = lines[
            i + 1
        ]

        if _looks_like_label_fragment(
            candidate
        ):
            continue

        if not is_field_label(
            candidate
        ):

            cleaned = clean_name(
                candidate
            )

            if cleaned:
                return cleaned

    return None


# ============================================================
# PAN FIELD EXTRACTION
# ============================================================

def extract_pan_fields(
    lines: list[str],
):

    pan_number = (
        extract_pan_number(
            lines
        )
    )

    return {
        "name": extract_name(
            lines
        ),

        "father_name": (
            extract_father_name(
                lines
            )
        ),

        "dob": extract_dob(
            lines
        ),

        "pan_number": pan_number,

        "id_number": pan_number,

        "gender": None,

        "aadhaar_number": None,

        "document_type": PAN,
    }


# ============================================================
# AADHAAR FIELD EXTRACTION
# ============================================================

def extract_aadhaar_fields(
    lines: list[str],
):

    # --------------------------------------------------------
    # Standard name extraction first.
    # --------------------------------------------------------

    aadhaar_name = extract_name(
        lines
    )

    # --------------------------------------------------------
    # Common Aadhaar layout fallback.
    # --------------------------------------------------------

    if not aadhaar_name:

        aadhaar_name = extract_aadhaar_name(
            lines
        )

    aadhaar_number = (
        extract_aadhaar_number(
            lines
        )
    )

    return {
        "name": aadhaar_name,

        "father_name": None,

        "dob": extract_dob(
            lines
        ),

        "gender": extract_gender(
            lines
        ),

        "aadhaar_number": (
            aadhaar_number
        ),

        "id_number": (
            aadhaar_number
        ),

        "pan_number": None,

        "document_type": AADHAAR,
    }


# ============================================================
# MAIN FIELD EXTRACTION
# ============================================================

def extract_fields(
    ocr_text: str,
    document_type: str | None = None,
) -> dict:

    lines = normalize_lines(
        ocr_text
    )

    detected_type = (
        document_type
        or detect_document_type(
            lines
        )
    )

    detected_type = (
        str(
            detected_type
        )
        .strip()
        .upper()
    )

    if detected_type == PAN:

        return extract_pan_fields(
            lines
        )

    if detected_type == AADHAAR:

        return extract_aadhaar_fields(
            lines
        )

    id_number = extract_id_number(
        lines
    )

    return {
        "name": extract_name(
            lines
        ),

        "father_name": None,

        "dob": extract_dob(
            lines
        ),

        "gender": extract_gender(
            lines
        ),

        "pan_number": (
            extract_pan_number(
                lines
            )
        ),

        "aadhaar_number": (
            extract_aadhaar_number(
                lines
            )
        ),

        "id_number": id_number,

        "document_type": UNKNOWN,
    }


# ============================================================
# FIELD COMPARISON
# ============================================================

def compare_fields(
    reference_fields: dict,
    submitted_fields: dict,
) -> dict:
    """
    Compare fields according to document type.

    PAN:
        name
        father_name
        dob
        pan_number

    Aadhaar:
        name
        dob
        gender
        aadhaar_number
    """

    if not reference_fields:
        reference_fields = {}

    if not submitted_fields:
        submitted_fields = {}

    reference_type = (
        str(
            reference_fields.get(
                "document_type",
                UNKNOWN,
            )
        )
        .strip()
        .upper()
    )

    submitted_type = (
        str(
            submitted_fields.get(
                "document_type",
                UNKNOWN,
            )
        )
        .strip()
        .upper()
    )

    if reference_type == PAN:

        screening_fields = [
            "name",
            "father_name",
            "dob",
            "pan_number",
        ]

    elif reference_type == AADHAAR:

        screening_fields = [
            "name",
            "dob",
            "gender",
            "aadhaar_number",
        ]

    else:

        screening_fields = [
            "name",
            "dob",
            "id_number",
            "gender",
        ]

    comparisons = {}

    mismatches = []

    for field in screening_fields:

        reference_value = (
            reference_fields.get(
                field
            )
        )

        submitted_value = (
            submitted_fields.get(
                field
            )
        )

        if (
            reference_value is None
            or str(
                reference_value
            ).strip() == ""
        ):
            continue

        reference_normalized = (
            normalize_field_value(
                field,
                reference_value,
            )
        )

        submitted_normalized = (
            normalize_field_value(
                field,
                submitted_value,
            )
        )

        if submitted_normalized is None:

            match = False
            match_reason = (
                "submitted_value_missing"
            )

        elif (
            reference_normalized
            == submitted_normalized
        ):

            match = True
            match_reason = (
                "exact_normalized_match"
            )

        else:

            match = False

            if field in {
                "pan_number",
                "aadhaar_number",
                "id_number",
            }:

                match_reason = (
                    "identity_number_mismatch"
                )

            elif field == "dob":

                match_reason = (
                    "date_of_birth_mismatch"
                )

            elif field in {
                "name",
                "father_name",
            }:

                match_reason = (
                    "name_mismatch"
                )

            elif field == "gender":

                match_reason = (
                    "gender_mismatch"
                )

            else:

                match_reason = (
                    "value_mismatch"
                )

        comparisons[field] = {
            "reference": reference_value,
            "submitted": submitted_value,
            "reference_normalized": (
                reference_normalized
            ),
            "submitted_normalized": (
                submitted_normalized
            ),
            "match": match,
            "match_reason": match_reason,
        }

        if not match:
            mismatches.append(
                field
            )

    total = len(
        comparisons
    )

    matched = sum(
        1
        for comparison in (
            comparisons.values()
        )
        if comparison["match"]
    )

    match_percentage = (
        (
            matched
            / total
        )
        * 100
        if total > 0
        else 100.0
    )

    document_type_match = (
        reference_type != UNKNOWN
        and submitted_type != UNKNOWN
        and reference_type
        == submitted_type
    )

    return {
        "comparisons": comparisons,
        "mismatches": mismatches,
        "matched_fields": matched,
        "total_fields": total,
        "match_percentage": round(
            match_percentage,
            2,
        ),
        "reference_document_type": (
            reference_type
        ),
        "submitted_document_type": (
            submitted_type
        ),
        "document_type_match": (
            document_type_match
        ),
    }