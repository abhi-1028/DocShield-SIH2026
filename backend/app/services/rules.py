import re


def normalize_text(value: str | None) -> str | None:
    """
    Normalize OCR text for reliable field comparison.
    """
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_name(value: str | None) -> str | None:
    """
    Normalize names such as:
        ARJUN SHARMA
        Arjun Sharma
        ARJUN
        SHARMA
    """
    value = normalize_text(value)

    if not value:
        return None

    return value.upper()


def normalize_dob(value: str | None) -> str | None:
    """
    Normalize dates into DD/MM/YYYY format.
    """
    value = normalize_text(value)

    if not value:
        return None

    match = re.search(
        r"(\d{2})[/-](\d{2})[/-](\d{4})",
        value,
    )

    if match:
        day, month, year = match.groups()
        return f"{day}/{month}/{year}"

    return value


def normalize_id(value: str | None) -> str | None:
    """
    Normalize document / ID numbers.
    """
    value = normalize_text(value)

    if not value:
        return None

    # Remove spaces and punctuation around the ID
    value = re.sub(r"[\s\-]+", "", value)

    return value.upper()


def extract_fields(ocr_text: str) -> dict:
    """
    Extract structured fields from OCR text.

    Designed to handle both:

        NAME: ARJUN SHARMA

    and OCR layouts where labels and values are on
    separate lines:

        FULL NAME
        ARJUN
        SHARMA

        DATE
        OF BIRTH
        14/08/2002

        ID NUMBER
        ABCDE1234F

        GENDER
        MALE
    """

    fields = {
        "name": None,
        "dob": None,
        "id_number": None,
        "gender": None,
    }

    # ---------------------------------------------------------
    # Clean OCR lines
    # ---------------------------------------------------------

    lines = [
        normalize_text(line)
        for line in ocr_text.splitlines()
        if normalize_text(line)
    ]

    # Uppercase copy makes matching easier
    upper_lines = [line.upper() for line in lines]

    # ---------------------------------------------------------
    # 1. DATE OF BIRTH
    # ---------------------------------------------------------

    # First try the simple same-line format:
    #
    # DOB: 14/08/2002
    # DATE OF BIRTH: 14/08/2002

    for line in lines:

        dob_match = re.search(
            r"(?:DOB|D\.O\.B|DATE\s+OF\s+BIRTH)"
            r"\s*[:\-]?\s*"
            r"(\d{2}[/-]\d{2}[/-]\d{4})",
            line,
            re.IGNORECASE,
        )

        if dob_match:
            fields["dob"] = normalize_dob(dob_match.group(1))
            break

    # If not found, handle OCR split across lines:
    #
    # DATE
    # OF BIRTH
    # 14/08/2002

    if fields["dob"] is None:

        for i, line in enumerate(upper_lines):

            if line == "DATE" and i + 2 < len(lines):

                if upper_lines[i + 1] == "OF BIRTH":

                    dob_match = re.search(
                        r"\d{2}[/-]\d{2}[/-]\d{4}",
                        lines[i + 2],
                    )

                    if dob_match:
                        fields["dob"] = normalize_dob(
                            dob_match.group(0)
                        )
                        break

            # Also handle:
            #
            # DATE OF
            # BIRTH
            # 14/08/2002

            if line == "DATE OF" and i + 2 < len(lines):

                if upper_lines[i + 1] == "BIRTH":

                    dob_match = re.search(
                        r"\d{2}[/-]\d{2}[/-]\d{4}",
                        lines[i + 2],
                    )

                    if dob_match:
                        fields["dob"] = normalize_dob(
                            dob_match.group(0)
                        )
                        break

    # Finally, if there is only one obvious date in the OCR,
    # use it as DOB.
    if fields["dob"] is None:

        for line in lines:

            dob_match = re.search(
                r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",
                line,
            )

            if dob_match:
                fields["dob"] = normalize_dob(
                    dob_match.group(0)
                )
                break

    # ---------------------------------------------------------
    # 2. GENDER
    # ---------------------------------------------------------

    for line in upper_lines:

        gender_match = re.fullmatch(
            r"(MALE|FEMALE|OTHER)",
            line,
            re.IGNORECASE,
        )

        if gender_match:
            fields["gender"] = gender_match.group(1).upper()
            break

    # ---------------------------------------------------------
    # 3. ID NUMBER
    # ---------------------------------------------------------

    # Same-line formats:
    #
    # ID NUMBER: ABCDE1234F
    # ID NO: ABCDE1234F

    for line in lines:

        id_match = re.search(
            r"(?:ID\s+NUMBER|ID\s+NO|ID|IDENTIFICATION\s+NO|"
            r"DOCUMENT\s+NO)"
            r"\s*[:\-]?\s*"
            r"([A-Z0-9]{4,})",
            line,
            re.IGNORECASE,
        )

        if id_match:

            candidate = normalize_id(id_match.group(1))

            # Don't accidentally treat "NUMBER" or labels
            # as the ID value.
            if candidate and candidate not in {
                "NUMBER",
                "NO",
            }:
                fields["id_number"] = candidate
                break

    # Split-line format:
    #
    # ID NUMBER
    # ABCDE1234F

    if fields["id_number"] is None:

        for i, line in enumerate(upper_lines):

            if line in {
                "ID NUMBER",
                "ID NO",
                "IDENTIFICATION NO",
                "DOCUMENT NO",
            }:

                if i + 1 < len(lines):

                    candidate = lines[i + 1]

                    # ID numbers normally contain letters/numbers.
                    # Ignore obvious unrelated labels.
                    if re.fullmatch(
                        r"[A-Z0-9\-]{4,}",
                        candidate.upper(),
                    ):

                        if candidate.upper() not in {
                            "REFERENCE",
                            "GENDER",
                            "MALE",
                            "FEMALE",
                            "PHOTO",
                        }:

                            fields["id_number"] = normalize_id(
                                candidate
                            )
                            break

    # ---------------------------------------------------------
    # 4. NAME
    # ---------------------------------------------------------

    # Same-line formats:
    #
    # NAME: ARJUN SHARMA
    # FULL NAME: ARJUN SHARMA

    for line in lines:

        name_match = re.search(
            r"(?:FULL\s+NAME|NAME)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE,
        )

        if name_match:

            candidate = name_match.group(1).strip()

            if candidate:
                fields["name"] = normalize_name(candidate)
                break

    # Split-line format:
    #
    # FULL NAME
    # ARJUN
    # SHARMA

    if fields["name"] is None:

        for i, line in enumerate(upper_lines):

            if line in {
                "FULL NAME",
                "NAME",
            }:

                name_parts = []

                # Look at the next few lines for name components.
                for j in range(i + 1, min(i + 4, len(lines))):

                    candidate = lines[j].strip()
                    candidate_upper = candidate.upper()

                    # Stop when another known field begins.
                    if candidate_upper in {
                        "DATE",
                        "DATE OF",
                        "OF BIRTH",
                        "BIRTH",
                        "ID NUMBER",
                        "ID NO",
                        "GENDER",
                        "PHOTO",
                        "REFERENCE ID",
                        "REFERENCE",
                        "STATUS",
                    }:
                        break

                    # Ignore dates
                    if re.search(
                        r"\d{2}[/-]\d{2}[/-]\d{4}",
                        candidate,
                    ):
                        break

                    # Names should primarily contain letters/spaces.
                    if re.fullmatch(
                        r"[A-Za-z][A-Za-z\s.'\-]*",
                        candidate,
                    ):

                        name_parts.append(candidate)

                    # Usually enough to get first + last name.
                    if len(name_parts) >= 3:
                        break

                if name_parts:

                    fields["name"] = normalize_name(
                        " ".join(name_parts)
                    )

                    break

    # ---------------------------------------------------------
    # Return extracted fields
    # ---------------------------------------------------------

    return fields


def compare_fields(
    reference_fields: dict,
    submitted_fields: dict,
) -> dict:
    """
    Compare extracted reference fields against submitted fields.
    """

    comparisons = {}
    mismatches = []

    for field in reference_fields:

        reference_value = reference_fields.get(field)
        submitted_value = submitted_fields.get(field)

        # Skip fields that don't exist in reference.
        if reference_value is None:
            continue

        # Normalize values before comparison.
        if field == "name":

            reference_normalized = normalize_name(
                reference_value
            )

            submitted_normalized = normalize_name(
                submitted_value
            )

        elif field == "dob":

            reference_normalized = normalize_dob(
                reference_value
            )

            submitted_normalized = normalize_dob(
                submitted_value
            )

        elif field == "id_number":

            reference_normalized = normalize_id(
                reference_value
            )

            submitted_normalized = normalize_id(
                submitted_value
            )

        else:

            reference_normalized = normalize_text(
                reference_value
            )

            submitted_normalized = normalize_text(
                submitted_value
            )

            if reference_normalized:
                reference_normalized = reference_normalized.upper()

            if submitted_normalized:
                submitted_normalized = submitted_normalized.upper()

        # Compare
        match = (
            reference_normalized is not None
            and submitted_normalized is not None
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
        "match_percentage": round(match_percentage, 2),
    }