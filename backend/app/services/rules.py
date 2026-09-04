import re


def extract_fields(ocr_text: str) -> dict:
    fields = {
        "name": None,
        "dob": None,
        "id_number": None,
        "gender": None,
    }

    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

    for line in lines:
        # Date of birth
        dob_match = re.search(
            r"(?:DOB|D\.O\.B|DATE OF BIRTH)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})",
            line,
            re.IGNORECASE,
        )
        if dob_match:
            fields["dob"] = dob_match.group(1)

        # Gender
        gender_match = re.search(
            r"\b(MALE|FEMALE|OTHER)\b",
            line,
            re.IGNORECASE,
        )
        if gender_match:
            fields["gender"] = gender_match.group(1).upper()

        # ID / document number
        id_match = re.search(
            r"(?:ID|ID NO|IDENTIFICATION NO|DOCUMENT NO)\s*[:\-]?\s*([A-Z0-9\-]{4,})",
            line,
            re.IGNORECASE,
        )
        if id_match:
            fields["id_number"] = id_match.group(1).upper()

    # Name is intentionally conservative.
    # We only infer it when an explicit "Name:" label exists.
    for line in lines:
        name_match = re.search(
            r"(?:NAME)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE,
        )
        if name_match:
            fields["name"] = name_match.group(1).strip()

    return fields


def compare_fields(reference_fields: dict, submitted_fields: dict) -> dict:
    comparisons = {}
    mismatches = []

    for field in reference_fields:
        reference_value = reference_fields.get(field)
        submitted_value = submitted_fields.get(field)

        if reference_value is None:
            continue

        match = (
            submitted_value is not None
            and str(reference_value).strip().upper()
            == str(submitted_value).strip().upper()
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
        1 for comparison in comparisons.values()
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
