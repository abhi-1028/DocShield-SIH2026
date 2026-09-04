import re


# ============================================================
# LINE NORMALIZATION
# ============================================================

def normalize_lines(ocr_text: str) -> list[str]:
    """
    Convert OCR output into clean, non-empty lines.
    """
    lines = []

    for line in ocr_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return lines


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_name(value: str) -> str:
    """
    Clean OCR noise from a person's name.
    """
    value = re.sub(r"[^A-Za-z .'-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def normalize_id(value: str):
    """
    Normalize ID values for comparison.

    Example:
        AB CD 123 -> ABCD123
    """
    if value is None:
        return None

    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def normalize_value(value):
    """
    Normalize general field values for comparison.
    """
    if value is None:
        return None

    value = str(value).strip().upper()
    value = re.sub(r"\s+", " ", value)

    return value


# ============================================================
# LABEL HELPERS
# ============================================================

def is_field_label(line: str) -> bool:
    """
    Determine whether an OCR line is a known field label.
    """

    normalized = re.sub(
        r"[^A-Z0-9 ]",
        "",
        line.upper(),
    ).strip()

    known_labels = {
        "FULL NAME",
        "NAME",
        "DATE",
        "OF BIRTH",
        "DATE OF BIRTH",
        "DOB",
        "D O B",
        "PHOTO",
        "ID NUMBER",
        "ID NO",
        "IDENTIFICATION NO",
        "DOCUMENT NO",
        "AADHAAR",
        "AADHAAR NO",
        "AADHAAR NUMBER",
        "GENDER",
        "REFERENCE ID",
        "ADDRESS",
    }

    return normalized in known_labels


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_dob(lines: list[str]):
    """
    Extract date of birth from OCR.

    Handles:

        DATE OF BIRTH: 14/08/2002

    and:

        DATE
        OF BIRTH
        14/08/2002

    and noisy OCR such as:

        DOB: 17,17/2010
    """

    for i, line in enumerate(lines):

        # ----------------------------------------------------
        # Case 1: DATE OF BIRTH: 14/08/2002
        # ----------------------------------------------------

        match = re.search(
            r"(?:DATE\s+OF\s+BIRTH|DOB|D\.O\.B)"
            r"\s*[:\-]?\s*"
            r"(\d{2}[/-]\d{2}[/-]\d{4})",
            line,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

        # ----------------------------------------------------
        # Case 2:
        #
        # DATE
        # OF BIRTH
        # 14/08/2002
        # ----------------------------------------------------

        if line.upper() == "DATE":

            if i + 2 < len(lines):

                if lines[i + 1].upper() == "OF BIRTH":

                    match = re.search(
                        r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b",
                        lines[i + 2],
                    )

                    if match:
                        return match.group(1)

        # ----------------------------------------------------
        # Case 3: noisy comma in date
        #
        # DOB: 17,17/2010
        # ----------------------------------------------------

        noisy_line = line.replace(",", "/")

        match = re.search(
            r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b",
            noisy_line,
        )

        if match:

            upper = line.upper()

            if (
                "DOB" in upper
                or "D.O.B" in upper
                or "DATE" in upper
            ):
                return (
                    f"{match.group(1)}/"
                    f"{match.group(2)}/"
                    f"{match.group(3)}"
                )

    return None


# ============================================================
# GENDER EXTRACTION
# ============================================================

def extract_gender(lines: list[str]):
    """
    Extract MALE / FEMALE / OTHER.
    """

    for i, line in enumerate(lines):

        # ----------------------------------------------------
        # Case 1: gender appears anywhere in a line
        # ----------------------------------------------------

        match = re.search(
            r"\b(MALE|FEMALE|OTHER)\b",
            line,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).upper()

        # ----------------------------------------------------
        # Case 2:
        #
        # GENDER
        # MALE
        # ----------------------------------------------------

        if line.upper() == "GENDER":

            if i + 1 < len(lines):

                candidate = lines[i + 1].strip().upper()

                if candidate in {
                    "MALE",
                    "FEMALE",
                    "OTHER",
                }:
                    return candidate

    return None


# ============================================================
# ID NUMBER EXTRACTION
# ============================================================

def extract_id_number(lines: list[str]):
    """
    Extract document / ID number.

    Handles:

        ID NUMBER
        ABCDE1234F

    and:

        ID NUMBER: ABCDE1234F

    and Aadhaar-style:

        6623 8349 1004

    IMPORTANT:
    We never treat the label 'ID NUMBER' itself as the value.
    """

    # --------------------------------------------------------
    # FIRST: Aadhaar-style 12 digit number
    # --------------------------------------------------------

    for line in lines:

        # Find groups of digits while allowing spaces.
        digit_groups = re.findall(
            r"\d[\d\s]{10,}\d",
            line,
        )

        for candidate in digit_groups:

            digits = re.sub(r"\D", "", candidate)

            if len(digits) == 12:
                return digits

    # --------------------------------------------------------
    # SECOND: explicit ID label
    # --------------------------------------------------------

    id_labels = {
        "ID NUMBER",
        "ID NO",
        "IDENTIFICATION NO",
        "DOCUMENT NO",
        "AADHAAR NO",
        "AADHAAR NUMBER",
    }

    for i, line in enumerate(lines):

        upper = line.upper().strip()

        # ----------------------------------------------------
        # Case 1:
        #
        # ID NUMBER: ABCDE1234F
        # ----------------------------------------------------

        match = re.search(
            r"(?:ID\s+NUMBER|ID\s+NO|IDENTIFICATION\s+NO|DOCUMENT\s+NO|AADHAAR\s+NO|AADHAAR\s+NUMBER)"
            r"\s*[:\-]\s*"
            r"([A-Z0-9][A-Z0-9\-]{3,})",
            line,
            re.IGNORECASE,
        )

        if match:

            candidate = match.group(1).upper()

            # Make sure it isn't just a label.
            if candidate not in {
                "IDNUMBER",
                "IDNO",
                "IDENTIFICATIONNO",
                "DOCUMENTNO",
                "AADHAARNO",
                "AADHAARNUMBER",
            }:
                return candidate

        # ----------------------------------------------------
        # Case 2:
        #
        # ID NUMBER
        # ABCDE1234F
        # ----------------------------------------------------

        if upper in id_labels:

            if i + 1 < len(lines):

                candidate = lines[i + 1].strip()

                candidate_upper = candidate.upper()

                # Don't accept another field label.
                if candidate_upper in id_labels:
                    continue

                if is_field_label(candidate):
                    continue

                cleaned = re.sub(
                    r"[^A-Z0-9\-]",
                    "",
                    candidate_upper,
                )

                if len(cleaned) >= 4:
                    return cleaned

    return None


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(lines: list[str]):
    """
    Extract a person's name.

    Handles:

        FULL NAME
        ARJUN
        SHARMA

    and:

        NAME: ARJUN SHARMA
    """

    # --------------------------------------------------------
    # Case 1: explicit FULL NAME / NAME label
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        upper = line.upper().strip()

        # ----------------------------------------------------
        # Same-line:
        #
        # NAME: ARJUN SHARMA
        # ----------------------------------------------------

        match = re.search(
            r"^(?:FULL\s+NAME|NAME)\s*[:\-]\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if match:

            cleaned = clean_name(match.group(1))

            if cleaned:
                return cleaned

        # ----------------------------------------------------
        # Separate-line:
        #
        # FULL NAME
        # ARJUN
        # SHARMA
        # ----------------------------------------------------

        if upper in {
            "FULL NAME",
            "NAME",
        }:

            name_parts = []

            # Look ahead a few lines.
            for candidate in lines[i + 1:i + 5]:

                candidate_upper = candidate.upper().strip()

                # Stop when another field begins.
                if candidate_upper in {
                    "DATE",
                    "OF BIRTH",
                    "DATE OF BIRTH",
                    "DOB",
                    "D.O.B",
                    "PHOTO",
                    "ID NUMBER",
                    "ID NO",
                    "IDENTIFICATION NO",
                    "DOCUMENT NO",
                    "GENDER",
                    "ADDRESS",
                    "REFERENCE ID",
                }:
                    break

                # Stop at a date.
                if re.search(
                    r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",
                    candidate,
                ):
                    break

                # Stop at a 12-digit ID.
                candidate_digits = re.sub(
                    r"\D",
                    "",
                    candidate,
                )

                if len(candidate_digits) == 12:
                    break

                cleaned = clean_name(candidate)

                if cleaned:
                    name_parts.append(cleaned)

            if name_parts:

                return " ".join(name_parts).strip()

    return None


# ============================================================
# MAIN FIELD EXTRACTION
# ============================================================

def extract_fields(ocr_text: str) -> dict:
    """
    Extract the four main screening fields.
    """

    fields = {
        "name": None,
        "dob": None,
        "id_number": None,
        "gender": None,
    }

    lines = normalize_lines(ocr_text)

    # Extract each field independently.
    fields["name"] = extract_name(lines)
    fields["dob"] = extract_dob(lines)
    fields["id_number"] = extract_id_number(lines)
    fields["gender"] = extract_gender(lines)

    return fields


# ============================================================
# FIELD COMPARISON
# ============================================================

def compare_fields(
    reference_fields: dict,
    submitted_fields: dict,
) -> dict:
    """
    Compare reference fields with submitted fields.
    """

    comparisons = {}
    mismatches = []

    for field in reference_fields:

        reference_value = reference_fields.get(field)
        submitted_value = submitted_fields.get(field)

        # Ignore reference fields that couldn't be extracted.
        if reference_value is None:
            continue

        # ----------------------------------------------------
        # ID comparison
        # ----------------------------------------------------

        if field == "id_number":

            reference_normalized = normalize_id(
                reference_value
            )

            submitted_normalized = normalize_id(
                submitted_value
            )

        # ----------------------------------------------------
        # Normal field comparison
        # ----------------------------------------------------

        else:

            reference_normalized = normalize_value(
                reference_value
            )

            submitted_normalized = normalize_value(
                submitted_value
            )

        match = (
            submitted_normalized is not None
            and reference_normalized == submitted_normalized
        )

        comparisons[field] = {
            "reference": reference_value,
            "submitted": submitted_value,
            "match": match,
        }

        if not match:
            mismatches.append(field)

    total = len(comparisons)

    matched = sum(
        1
        for comparison in comparisons.values()
        if comparison["match"]
    )

    match_percentage = (
        (matched / total) * 100
        if total > 0
        else 100.0
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
    }