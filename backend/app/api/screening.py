from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.comparison import (
    compare_documents,
    list_reference_images,
)
from app.services.ocr import extract_text
from app.services.risk_engine import calculate_risk
from app.services.tamper_detection import detect_tampered_regions
from app.services.fields import extract_fields, compare_fields
from app.services.document_type import (
    detect_document_type,
    PAN,
    AADHAAR,
    UNKNOWN,
)
from app.services.qr_mrz import scan_document_qr


router = APIRouter(
    prefix="/api",
    tags=["Document Screening"],
)

BACKEND_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BACKEND_DIR / "uploads"

REFERENCE_DIR = (
    BACKEND_DIR / "reference_documents"
)

TAMPER_OUTPUT_DIR = (
    BACKEND_DIR / "tamper_outputs"
)


# ============================================================
# REFERENCE ANALYSIS CACHE
# ============================================================

_REFERENCE_ANALYSIS_CACHE = {}


def _get_reference_cache_signature(path: Path):
    """
    Return a lightweight signature used to detect
    modifications to a reference document.
    """

    try:
        stat = path.stat()

        return (
            stat.st_mtime_ns,
            stat.st_size,
        )

    except OSError:
        return None


def _get_cached_reference_analysis(path: Path):
    """
    Cache OCR, document type detection, field extraction,
    and QR scanning for reference documents.

    The cache automatically refreshes if the reference file
    changes.
    """

    signature = _get_reference_cache_signature(path)

    if signature is None:
        raise ValueError(
            f"Unable to access reference document: {path}"
        )

    cache_key = str(path.resolve())

    cached = _REFERENCE_ANALYSIS_CACHE.get(
        cache_key
    )

    if (
        cached is not None
        and cached.get("signature") == signature
    ):
        return cached["analysis"]

    name_hint = _reference_type_from_name(
        path
    )

    reference_ocr = extract_text(
        str(path)
    )

    reference_type_result = detect_document_type(
        reference_ocr["text"]
    )

    detected_type = (
        reference_type_result["document_type"]
    )

    reference_type = (
        name_hint or detected_type
    )

    reference_fields = extract_fields(
        reference_ocr["text"],
        reference_type,
    )

    # --------------------------------------------------------
    # QR analysis for the reference document.
    #
    # QR scanning is cached so the reference QR does not need
    # to be decoded again for every submitted document.
    # --------------------------------------------------------

    try:
        reference_qr = scan_document_qr(
            str(path)
        )
    except Exception:
        reference_qr = _empty_qr_result(
            reference_type
        )

    analysis = {
        "reference_ocr": reference_ocr,
        "reference_type_result": (
            reference_type_result
        ),
        "reference_type": reference_type,
        "reference_fields": reference_fields,
        "reference_qr": reference_qr,
    }

    _REFERENCE_ANALYSIS_CACHE[
        cache_key
    ] = {
        "signature": signature,
        "analysis": analysis,
    }

    return analysis


# ============================================================
# EMPTY RESPONSES
# ============================================================

def _empty_field_comparison(
    reference_type=UNKNOWN,
    submitted_type=UNKNOWN,
):
    return {
        "comparisons": {},
        "mismatches": [],
        "matched_fields": 0,
        "total_fields": 0,
        "match_percentage": 0,
        "reference_document_type": (
            reference_type
        ),
        "submitted_document_type": (
            submitted_type
        ),
        "document_type_match": (
            reference_type
            == submitted_type
            != UNKNOWN
        ),
    }


def _empty_tamper_evidence():
    return {
        "suspicious_region_count": 0,
        "suspicious_regions": [],
        "highlighted_image_url": None,
        "tamper_confidence": 0.0,
    }


def _empty_qr_result(
    document_type=None,
):
    """
    Standard empty QR structure.

    QR failure is intentionally represented as NOT_AVAILABLE
    rather than as fraud.
    """

    return {
        "detected": False,
        "codes_detected": 0,
        "codes": [],
        "document_type": document_type,
        "identity_number": None,
        "name": None,
        "dob": None,
        "gender": None,
        "raw_payload": None,
    }


def _empty_qr_verification():
    """
    Standard QR verification response.
    """

    return {
        "status": "NOT_AVAILABLE",
        "reference_detected": False,
        "submitted_detected": False,
        "reference_document_type": None,
        "submitted_document_type": None,
        "reference_identity_number": None,
        "submitted_identity_number": None,
        "submitted_ocr_identity_number": None,
        "reference_qr_match": None,
        "visible_number_qr_match": None,
        "identity_number_match": None,
        "message": (
            "QR verification was not available for this "
            "screening result."
        ),
        "reference": _empty_qr_result(),
        "submitted": _empty_qr_result(),
    }


# ============================================================
# REFERENCE TYPE
# ============================================================

def _reference_type_from_name(
    path: Path,
):
    """
    Use filename hints first.
    OCR remains the fallback.
    """

    name = (
        path.stem
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    if (
        "aadhaar" in name
        or "aadhar" in name
    ):
        return AADHAAR

    if "pan" in name:
        return PAN

    return None


# ============================================================
# QR HELPERS
# ============================================================

def _get_qr_identity_number(
    qr_result: dict | None,
):
    """
    Return the best identity number extracted from a QR result.
    """

    if not qr_result:
        return None

    value = qr_result.get(
        "identity_number"
    )

    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _get_qr_document_type(
    qr_result: dict | None,
):
    if not qr_result:
        return None

    value = qr_result.get(
        "document_type"
    )

    if value is None:
        return None

    value = (
        str(value)
        .strip()
        .upper()
    )

    return value if value else None


def _verify_qr(
    reference_qr: dict | None,
    submitted_qr: dict | None,
    submitted_fields: dict | None,
    document_type: str,
):
    """
    Compare the reference QR, submitted QR, and visible OCR
    identity number.

    The QR layer is an additional verification signal.

    Possible statuses:

        MATCH
        MISMATCH
        NOT_AVAILABLE
        INCONSISTENT

    INCONSISTENT is used when the submitted document contains
    a QR identity number that disagrees with its visible OCR
    identity number.

    QR decoding failure alone never becomes fraud evidence.
    """

    reference_qr = (
        reference_qr
        or _empty_qr_result(
            document_type
        )
    )

    submitted_qr = (
        submitted_qr
        or _empty_qr_result(
            document_type
        )
    )

    submitted_fields = (
        submitted_fields
        or {}
    )

    reference_identity = (
        _get_qr_identity_number(
            reference_qr
        )
    )

    submitted_identity = (
        _get_qr_identity_number(
            submitted_qr
        )
    )

    if document_type == PAN:

        submitted_ocr_identity = (
            submitted_fields.get(
                "pan_number"
            )
        )

    elif document_type == AADHAAR:

        submitted_ocr_identity = (
            submitted_fields.get(
                "aadhaar_number"
            )
        )

    else:

        submitted_ocr_identity = (
            submitted_fields.get(
                "id_number"
            )
        )

    if (
        submitted_ocr_identity is not None
    ):

        submitted_ocr_identity = str(
            submitted_ocr_identity
        ).strip()

    # --------------------------------------------------------
    # Reference QR vs submitted QR.
    # --------------------------------------------------------

    reference_qr_match = None

    if (
        reference_identity
        and submitted_identity
    ):

        reference_qr_match = (
            reference_identity
            == submitted_identity
        )

    # --------------------------------------------------------
    # Submitted visible identity vs submitted QR.
    # --------------------------------------------------------

    visible_number_qr_match = None

    if (
        submitted_ocr_identity
        and submitted_identity
    ):

        visible_number_qr_match = (
            submitted_ocr_identity
            == submitted_identity
        )

    # --------------------------------------------------------
    # No QR information available.
    # --------------------------------------------------------

    if not reference_identity and not submitted_identity:

        result = _empty_qr_verification()

        result[
            "reference_document_type"
        ] = _get_qr_document_type(
            reference_qr
        )

        result[
            "submitted_document_type"
        ] = _get_qr_document_type(
            submitted_qr
        )

        result[
            "submitted_ocr_identity_number"
        ] = submitted_ocr_identity

        result[
            "reference"
        ] = reference_qr

        result[
            "submitted"
        ] = submitted_qr

        result[
            "message"
        ] = (
            "No usable QR identity data was available. "
            "QR verification was not used as a fraud signal."
        )

        return result

    # --------------------------------------------------------
    # Submitted QR conflicts with visible identity number.
    #
    # This is the most important new integrity check.
    # --------------------------------------------------------

    if (
        visible_number_qr_match is False
    ):

        return {
            "status": "INCONSISTENT",
            "reference_detected": bool(
                reference_qr.get(
                    "detected",
                    False,
                )
            ),
            "submitted_detected": bool(
                submitted_qr.get(
                    "detected",
                    False,
                )
            ),
            "reference_document_type": (
                _get_qr_document_type(
                    reference_qr
                )
            ),
            "submitted_document_type": (
                _get_qr_document_type(
                    submitted_qr
                )
            ),
            "reference_identity_number": (
                reference_identity
            ),
            "submitted_identity_number": (
                submitted_identity
            ),
            "submitted_ocr_identity_number": (
                submitted_ocr_identity
            ),
            "reference_qr_match": (
                reference_qr_match
            ),
            "visible_number_qr_match": (
                False
            ),
            "identity_number_match": (
                False
            ),
            "message": (
                "The visible identity number does not match "
                "the identity number encoded in the submitted "
                "QR code."
            ),
            "reference": reference_qr,
            "submitted": submitted_qr,
        }

    # --------------------------------------------------------
    # Reference QR and submitted QR both exist and match.
    # --------------------------------------------------------

    if (
        reference_qr_match is True
        and visible_number_qr_match is True
    ):

        return {
            "status": "MATCH",
            "reference_detected": True,
            "submitted_detected": True,
            "reference_document_type": (
                _get_qr_document_type(
                    reference_qr
                )
            ),
            "submitted_document_type": (
                _get_qr_document_type(
                    submitted_qr
                )
            ),
            "reference_identity_number": (
                reference_identity
            ),
            "submitted_identity_number": (
                submitted_identity
            ),
            "submitted_ocr_identity_number": (
                submitted_ocr_identity
            ),
            "reference_qr_match": True,
            "visible_number_qr_match": True,
            "identity_number_match": True,
            "message": (
                "The submitted QR identity data is consistent "
                "with both the authorized reference and the "
                "visible identity number."
            ),
            "reference": reference_qr,
            "submitted": submitted_qr,
        }

    # --------------------------------------------------------
    # QR exists but differs from reference.
    # --------------------------------------------------------

    if (
        reference_qr_match is False
    ):

        return {
            "status": "MISMATCH",
            "reference_detected": bool(
                reference_qr.get(
                    "detected",
                    False,
                )
            ),
            "submitted_detected": bool(
                submitted_qr.get(
                    "detected",
                    False,
                )
            ),
            "reference_document_type": (
                _get_qr_document_type(
                    reference_qr
                )
            ),
            "submitted_document_type": (
                _get_qr_document_type(
                    submitted_qr
                )
            ),
            "reference_identity_number": (
                reference_identity
            ),
            "submitted_identity_number": (
                submitted_identity
            ),
            "submitted_ocr_identity_number": (
                submitted_ocr_identity
            ),
            "reference_qr_match": False,
            "visible_number_qr_match": (
                visible_number_qr_match
            ),
            "identity_number_match": False,
            "message": (
                "The identity information encoded in the "
                "submitted QR code does not match the "
                "authorized reference QR data."
            ),
            "reference": reference_qr,
            "submitted": submitted_qr,
        }

    # --------------------------------------------------------
    # A QR identity exists but the corresponding reference
    # identity was unavailable.
    # --------------------------------------------------------

    if submitted_identity:

        return {
            "status": "AVAILABLE",
            "reference_detected": bool(
                reference_qr.get(
                    "detected",
                    False,
                )
            ),
            "submitted_detected": bool(
                submitted_qr.get(
                    "detected",
                    False,
                )
            ),
            "reference_document_type": (
                _get_qr_document_type(
                    reference_qr
                )
            ),
            "submitted_document_type": (
                _get_qr_document_type(
                    submitted_qr
                )
            ),
            "reference_identity_number": (
                reference_identity
            ),
            "submitted_identity_number": (
                submitted_identity
            ),
            "submitted_ocr_identity_number": (
                submitted_ocr_identity
            ),
            "reference_qr_match": (
                reference_qr_match
            ),
            "visible_number_qr_match": (
                visible_number_qr_match
            ),
            "identity_number_match": (
                visible_number_qr_match
            ),
            "message": (
                "QR identity information was decoded from the "
                "submitted document, but a reference QR identity "
                "was not available for a full QR-to-reference check."
            ),
            "reference": reference_qr,
            "submitted": submitted_qr,
        }

    return {
        "status": "NOT_AVAILABLE",
        "reference_detected": bool(
            reference_qr.get(
                "detected",
                False,
            )
        ),
        "submitted_detected": bool(
            submitted_qr.get(
                "detected",
                False,
            )
        ),
        "reference_document_type": (
            _get_qr_document_type(
                reference_qr
            )
        ),
        "submitted_document_type": (
            _get_qr_document_type(
                submitted_qr
            )
        ),
        "reference_identity_number": (
            reference_identity
        ),
        "submitted_identity_number": (
            submitted_identity
        ),
        "submitted_ocr_identity_number": (
            submitted_ocr_identity
        ),
        "reference_qr_match": (
            reference_qr_match
        ),
        "visible_number_qr_match": (
            visible_number_qr_match
        ),
        "identity_number_match": (
            visible_number_qr_match
        ),
        "message": (
            "QR verification did not produce enough identity "
            "information for a definitive comparison."
        ),
        "reference": reference_qr,
        "submitted": submitted_qr,
    }


# ============================================================
# CANDIDATE SCORING
# ============================================================

def _candidate_match_score(
    field_comparison: dict,
    visual_similarity: float,
):
    """
    Calculate a repository candidate score.

    Exact identity-number matches remain the strongest match.

    A strong contextual match is also accepted so that a
    document with a deliberately altered Aadhaar/PAN number
    can still be linked to the correct repository record and
    the changed identity number can be flagged as a mismatch.

    Returns:

        match_score
        identity_match
        contextual_match
    """

    field_percentage = float(
        field_comparison.get(
            "match_percentage",
            0,
        )
        or 0
    )

    comparisons = (
        field_comparison.get(
            "comparisons",
            {},
        )
        or {}
    )

    # --------------------------------------------------------
    # Identity-number comparison.
    # --------------------------------------------------------

    identity_field = None

    for field_name in (
        "pan_number",
        "aadhaar_number",
        "id_number",
    ):

        candidate = comparisons.get(
            field_name
        )

        if candidate:
            identity_field = candidate
            break

    identity_match = bool(
        identity_field
        and identity_field.get(
            "match"
        )
        is True
    )

    # --------------------------------------------------------
    # Contextual fields.
    # --------------------------------------------------------

    document_type = str(
        field_comparison.get(
            "reference_document_type",
            UNKNOWN,
        )
        or UNKNOWN
    ).strip().upper()

    if document_type == PAN:

        contextual_fields = [
            "name",
            "father_name",
            "dob",
        ]

    elif document_type == AADHAAR:

        contextual_fields = [
            "name",
            "dob",
            "gender",
        ]

    else:

        contextual_fields = [
            "name",
            "dob",
            "gender",
        ]

    contextual_comparisons = []

    for field_name in contextual_fields:

        comparison = comparisons.get(
            field_name
        )

        if comparison is None:
            continue

        reference_value = comparison.get(
            "reference"
        )

        if (
            reference_value is None
            or str(
                reference_value
            ).strip() == ""
        ):
            continue

        contextual_comparisons.append(
            comparison
        )

    contextual_available = len(
        contextual_comparisons
    )

    contextual_matched = sum(
        1
        for comparison in contextual_comparisons
        if comparison.get(
            "match"
        )
        is True
    )

    contextual_mismatched = sum(
        1
        for comparison in contextual_comparisons
        if comparison.get(
            "match"
        )
        is False
    )

    # --------------------------------------------------------
    # Strong contextual match.
    # --------------------------------------------------------

    contextual_match = (
        contextual_available >= 2
        and contextual_matched >= 2
        and contextual_mismatched == 0
    )

    # --------------------------------------------------------
    # Score.
    # --------------------------------------------------------

    if identity_match:

        score = (
            90.0
            + (
                float(visual_similarity)
                * 0.10
            )
        )

    elif contextual_match:

        contextual_ratio = (
            contextual_matched
            / contextual_available
        )

        score = (
            70.0
            + (
                contextual_ratio
                * 15.0
            )
            + (
                float(visual_similarity)
                * 0.15
            )
        )

    else:

        score = (
            field_percentage * 0.65
            + float(visual_similarity) * 0.35
        )

    return (
        round(
            min(
                100.0,
                max(
                    0.0,
                    score,
                ),
            ),
            2,
        ),
        identity_match,
        contextual_match,
    )


# ============================================================
# REPOSITORY MATCH GATE
# ============================================================

def _is_valid_repository_match(
    candidate: dict,
):
    """
    Decide whether a candidate is an authorized repository
    record.

    Valid:

        1. Exact identity-number match.

        OR

        2. Strong contextual/person-field match plus
           sufficient visual similarity.

    Visual similarity by itself is never enough.
    """

    if candidate.get(
        "identity_match",
        False,
    ):
        return True

    if not candidate.get(
        "contextual_match",
        False,
    ):
        return False

    visual = (
        candidate.get(
            "visual",
            {},
        )
        or {}
    )

    try:

        visual_similarity = float(
            visual.get(
                "similarity_score",
                0,
            )
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        visual_similarity = 0.0

    return visual_similarity >= 60.0


# ============================================================
# UPLOADED FILE
# ============================================================

def _get_uploaded_file(
    document_id: str,
):
    if not UPLOAD_DIR.exists():
        return None

    for file in UPLOAD_DIR.iterdir():

        if (
            file.is_file()
            and file.stem == document_id
        ):
            return file

    return None


# ============================================================
# SCREENING
# ============================================================

@router.post(
    "/screen/{document_id}"
)
def screen_document(
    document_id: str,
    expected_document_type: str | None = None,
):

    if expected_document_type is not None:

        expected_document_type = (
            expected_document_type
            .strip()
            .upper()
        )

        if expected_document_type not in (
            PAN,
            AADHAAR,
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid expected document type. "
                    "Use PAN or AADHAAR."
                ),
            )

    uploaded_file = _get_uploaded_file(
        document_id
    )

    if uploaded_file is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    try:

        # ====================================================
        # SUBMITTED OCR
        # ====================================================

        submitted_ocr = extract_text(
            str(uploaded_file)
        )

        submitted_type_result = (
            detect_document_type(
                submitted_ocr["text"]
            )
        )

        submitted_document_type = (
            submitted_type_result[
                "document_type"
            ]
        )

        # ====================================================
        # SUBMITTED QR
        # ====================================================

        try:

            submitted_qr = scan_document_qr(
                str(uploaded_file)
            )

        except Exception:

            submitted_qr = _empty_qr_result(
                submitted_document_type
            )

        # ====================================================
        # UNKNOWN DOCUMENT
        # ====================================================

        if submitted_document_type == UNKNOWN:

            return {
                "document_id": document_id,
                "expected_document_type": (
                    expected_document_type
                ),
                "uploaded_document_type": UNKNOWN,
                "document_type_match": False,
                "document_type_detection": {
                    "reference": None,
                    "submitted": (
                        submitted_type_result
                    ),
                },
                "decision": "INVALID DOCUMENT",
                "risk_score": 0,
                "similarity_score": 0,
                "difference_percentage": 100,
                "visual_integrity": {
                    "score": 0,
                    "similarity_score": 0,
                    "difference_percentage": 100,
                },
                "message": (
                    "The uploaded image could not be "
                    "confidently identified as a supported "
                    "document type."
                ),
                "ocr": {
                    "reference": None,
                    "submitted": submitted_ocr,
                },
                "field_comparison": (
                    _empty_field_comparison(
                        expected_document_type
                        or UNKNOWN,
                        UNKNOWN,
                    )
                ),
                "qr_verification": {
                    **_empty_qr_verification(),
                    "submitted": submitted_qr,
                },
                "tamper_evidence": (
                    _empty_tamper_evidence()
                ),
                "reference_match": {
                    "matched": False,
                    "matched_reference": None,
                    "match_score": 0,
                    "identity_match": False,
                    "contextual_match": False,
                    "reference_count_checked": 0,
                    "candidates": [],
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "document_type_points": 0,
                    "visual_difference_percentage": 100,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                    "tamper_confidence": 0,
                    "document_type_mismatch": True,
                },
            }

        # ====================================================
        # SELECT DOCUMENT TYPE
        # ====================================================

        if (
            expected_document_type is not None
            and submitted_document_type
            != expected_document_type
        ):

            selected_type = (
                expected_document_type
            )

        else:

            selected_type = (
                submitted_document_type
            )

        # ====================================================
        # TYPE MISMATCH
        # ====================================================

        if (
            submitted_document_type
            != selected_type
        ):

            return {
                "document_id": document_id,
                "expected_document_type": (
                    selected_type
                ),
                "uploaded_document_type": (
                    submitted_document_type
                ),
                "document_type_match": False,
                "document_type_detection": {
                    "reference": None,
                    "submitted": (
                        submitted_type_result
                    ),
                },
                "decision": "MANUAL REVIEW",
                "risk_score": 10.0,
                "similarity_score": None,
                "difference_percentage": None,
                "visual_integrity": {
                    "score": None,
                    "similarity_score": None,
                    "difference_percentage": None,
                },
                "message": (
                    f"Document type mismatch. Expected "
                    f"{selected_type} but detected "
                    f"{submitted_document_type}."
                ),
                "ocr": {
                    "reference": None,
                    "submitted": submitted_ocr,
                },
                "field_comparison": (
                    _empty_field_comparison(
                        selected_type,
                        submitted_document_type,
                    )
                ),
                "qr_verification": {
                    **_empty_qr_verification(),
                    "submitted": submitted_qr,
                },
                "tamper_evidence": (
                    _empty_tamper_evidence()
                ),
                "reference_match": {
                    "matched": False,
                    "matched_reference": None,
                    "match_score": 0,
                    "identity_match": False,
                    "contextual_match": False,
                    "reference_count_checked": 0,
                    "candidates": [],
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "document_type_points": 10.0,
                    "visual_difference_percentage": 0,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                    "tamper_confidence": 0,
                    "document_type_mismatch": True,
                },
            }

        # ====================================================
        # SUBMITTED FIELDS
        # ====================================================

        submitted_fields = extract_fields(
            submitted_ocr["text"],
            submitted_document_type,
        )

        submitted_field_count = sum(
            1
            for value in submitted_fields.values()
            if (
                value is not None
                and str(value).strip()
            )
        )

        if submitted_field_count < 2:

            return {
                "document_id": document_id,
                "expected_document_type": (
                    selected_type
                ),
                "uploaded_document_type": (
                    submitted_document_type
                ),
                "document_type_match": True,
                "document_type_detection": {
                    "reference": None,
                    "submitted": (
                        submitted_type_result
                    ),
                },
                "decision": "INVALID DOCUMENT",
                "risk_score": 0,
                "similarity_score": 0,
                "difference_percentage": 100,
                "visual_integrity": {
                    "score": 0,
                    "similarity_score": 0,
                    "difference_percentage": 100,
                },
                "message": (
                    "The uploaded image does not contain enough "
                    "recognizable document information for "
                    "reliable screening."
                ),
                "ocr": {
                    "reference": None,
                    "submitted": submitted_ocr,
                },
                "field_comparison": (
                    _empty_field_comparison(
                        selected_type,
                        submitted_document_type,
                    )
                ),
                "qr_verification": {
                    **_empty_qr_verification(),
                    "submitted": submitted_qr,
                },
                "tamper_evidence": (
                    _empty_tamper_evidence()
                ),
                "reference_match": {
                    "matched": False,
                    "matched_reference": None,
                    "match_score": 0,
                    "identity_match": False,
                    "contextual_match": False,
                    "reference_count_checked": 0,
                    "candidates": [],
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "document_type_points": 0,
                    "visual_difference_percentage": 100,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                    "tamper_confidence": 0,
                    "document_type_mismatch": False,
                },
            }

        # ====================================================
        # REFERENCE CANDIDATES
        # ====================================================

        candidates = []

        for reference_file in list_reference_images(
            REFERENCE_DIR
        ):

            try:

                reference_analysis = (
                    _get_cached_reference_analysis(
                        reference_file
                    )
                )

                reference_ocr = (
                    reference_analysis[
                        "reference_ocr"
                    ]
                )

                reference_type_result = (
                    reference_analysis[
                        "reference_type_result"
                    ]
                )

                reference_type = (
                    reference_analysis[
                        "reference_type"
                    ]
                )

                reference_fields = (
                    reference_analysis[
                        "reference_fields"
                    ]
                )

                reference_qr = (
                    reference_analysis[
                        "reference_qr"
                    ]
                )

                if (
                    reference_type
                    != selected_type
                ):
                    continue

                # ------------------------------------------------
                # Compare fields.
                # ------------------------------------------------

                field_comparison = compare_fields(
                    reference_fields,
                    submitted_fields,
                )

                # ------------------------------------------------
                # Visual comparison.
                # ------------------------------------------------

                visual = compare_documents(
                    str(reference_file),
                    str(uploaded_file),
                )

                # ------------------------------------------------
                # Candidate ranking.
                # ------------------------------------------------

                (
                    match_score,
                    identity_match,
                    contextual_match,
                ) = _candidate_match_score(
                    field_comparison,
                    visual[
                        "similarity_score"
                    ],
                )

                candidates.append(
                    {
                        "reference_file": (
                            reference_file
                        ),
                        "reference_ocr": (
                            reference_ocr
                        ),
                        "reference_type_result": (
                            reference_type_result
                        ),
                        "reference_fields": (
                            reference_fields
                        ),
                        "reference_qr": (
                            reference_qr
                        ),
                        "field_comparison": (
                            field_comparison
                        ),
                        "visual": visual,
                        "match_score": (
                            match_score
                        ),
                        "identity_match": (
                            identity_match
                        ),
                        "contextual_match": (
                            contextual_match
                        ),
                    }
                )

            except Exception:
                continue

        # ====================================================
        # NO REFERENCE TYPE AVAILABLE
        # ====================================================

        if not candidates:

            return {
                "document_id": document_id,
                "expected_document_type": (
                    selected_type
                ),
                "uploaded_document_type": (
                    submitted_document_type
                ),
                "document_type_match": True,
                "document_type_detection": {
                    "reference": None,
                    "submitted": (
                        submitted_type_result
                    ),
                },
                "decision": "NO DATA FOUND",
                "risk_score": 0,
                "similarity_score": None,
                "difference_percentage": None,
                "visual_integrity": {
                    "score": None,
                    "similarity_score": None,
                    "difference_percentage": None,
                },
                "message": (
                    f"No {selected_type} reference data "
                    "was found in the authorized reference "
                    "repository."
                ),
                "ocr": {
                    "reference": None,
                    "submitted": submitted_ocr,
                },
                "field_comparison": (
                    _empty_field_comparison(
                        selected_type,
                        submitted_document_type,
                    )
                ),
                "qr_verification": {
                    **_empty_qr_verification(),
                    "submitted": submitted_qr,
                },
                "tamper_evidence": (
                    _empty_tamper_evidence()
                ),
                "reference_match": {
                    "matched": False,
                    "matched_reference": None,
                    "match_score": 0,
                    "identity_match": False,
                    "contextual_match": False,
                    "reference_count_checked": 0,
                    "candidates": [],
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "document_type_points": 0,
                    "visual_difference_percentage": 0,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                    "tamper_confidence": 0,
                    "document_type_mismatch": False,
                },
            }

        # ====================================================
        # SORT CANDIDATES
        # ====================================================

        candidates.sort(
            key=lambda item:
            item["match_score"],
            reverse=True,
        )

        best = candidates[0]

        # ====================================================
        # REPOSITORY MATCH GATE
        # ====================================================

        valid_matches = [
            candidate
            for candidate in candidates
            if _is_valid_repository_match(
                candidate
            )
        ]

        if not valid_matches:

            return {
                "document_id": document_id,
                "expected_document_type": (
                    selected_type
                ),
                "uploaded_document_type": (
                    submitted_document_type
                ),
                "document_type_match": True,
                "document_type_detection": {
                    "reference": None,
                    "submitted": (
                        submitted_type_result
                    ),
                },
                "decision": "NO DATA FOUND",
                "risk_score": 0,
                "similarity_score": None,
                "difference_percentage": None,
                "visual_integrity": {
                    "score": None,
                    "similarity_score": None,
                    "difference_percentage": None,
                },
                "message": (
                    "No matching reference data was found "
                    "for the submitted document in the "
                    "authorized reference repository."
                ),
                "ocr": {
                    "reference": None,
                    "submitted": submitted_ocr,
                },
                "field_comparison": (
                    _empty_field_comparison(
                        selected_type,
                        submitted_document_type,
                    )
                ),
                "qr_verification": {
                    **_empty_qr_verification(),
                    "submitted": submitted_qr,
                },
                "tamper_evidence": (
                    _empty_tamper_evidence()
                ),
                "reference_match": {
                    "matched": False,
                    "matched_reference": None,
                    "match_score": (
                        best["match_score"]
                    ),
                    "identity_match": (
                        best["identity_match"]
                    ),
                    "contextual_match": (
                        best["contextual_match"]
                    ),
                    "reference_count_checked": (
                        len(candidates)
                    ),
                    "candidates": [
                        {
                            "filename": item[
                                "reference_file"
                            ].name,
                            "match_score": item[
                                "match_score"
                            ],
                            "visual_similarity": (
                                item["visual"][
                                    "similarity_score"
                                ]
                            ),
                            "field_match_percentage": (
                                item[
                                    "field_comparison"
                                ].get(
                                    "match_percentage",
                                    0,
                                )
                            ),
                            "identity_match": (
                                item[
                                    "identity_match"
                                ]
                            ),
                            "contextual_match": (
                                item[
                                    "contextual_match"
                                ]
                            ),
                        }
                        for item in candidates
                    ],
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "document_type_points": 0,
                    "visual_difference_percentage": 0,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                    "tamper_confidence": 0,
                    "document_type_mismatch": False,
                    "reference_identity_match": False,
                },
            }

        # ====================================================
        # SELECT BEST VALID REPOSITORY MATCH
        # ====================================================

        valid_matches.sort(
            key=lambda item: (
                item["identity_match"],
                item["match_score"],
            ),
            reverse=True,
        )

        best = valid_matches[0]

        reference_file = (
            best["reference_file"]
        )

        reference_ocr = (
            best["reference_ocr"]
        )

        reference_type_result = (
            best["reference_type_result"]
        )

        reference_qr = (
            best["reference_qr"]
        )

        comparison = best["visual"]

        field_comparison = (
            best["field_comparison"]
        )

        field_comparison[
            "reference_document_type"
        ] = selected_type

        field_comparison[
            "submitted_document_type"
        ] = submitted_document_type

        # ====================================================
        # QR VERIFICATION
        # ====================================================

        qr_verification = _verify_qr(
            reference_qr=reference_qr,
            submitted_qr=submitted_qr,
            submitted_fields=submitted_fields,
            document_type=selected_type,
        )

        # ====================================================
        # REFERENCE MATCH
        # ====================================================

        reference_match_threshold = 70.0

        reference_match = {
            "matched": (
                best["match_score"]
                >= reference_match_threshold
            ),
            "matched_reference": (
                reference_file.name
            ),
            "match_score": (
                best["match_score"]
            ),
            "identity_match": (
                best["identity_match"]
            ),
            "contextual_match": (
                best["contextual_match"]
            ),
            "reference_count_checked": (
                len(candidates)
            ),
            "candidates": [
                {
                    "filename": item[
                        "reference_file"
                    ].name,
                    "match_score": item[
                        "match_score"
                    ],
                    "visual_similarity": (
                        item["visual"][
                            "similarity_score"
                        ]
                    ),
                    "field_match_percentage": (
                        item[
                            "field_comparison"
                        ].get(
                            "match_percentage",
                            0,
                        )
                    ),
                    "identity_match": item[
                        "identity_match"
                    ],
                    "contextual_match": item[
                        "contextual_match"
                    ],
                }
                for item in candidates
            ],
        }

        # ====================================================
        # TAMPER DETECTION
        # ====================================================

        tamper_result = detect_tampered_regions(
            reference_path=str(
                reference_file
            ),
            uploaded_path=str(
                uploaded_file
            ),
            output_directory=str(
                TAMPER_OUTPUT_DIR
            ),
            field_comparison=(
                field_comparison
            ),
            submitted_ocr=(
                submitted_ocr
            ),
        )

        # ====================================================
        # RISK
        # ====================================================

        risk = calculate_risk(
            similarity_score=(
                comparison[
                    "similarity_score"
                ]
            ),
            field_comparison=(
                field_comparison
            ),
            tamper_evidence=(
                tamper_result
            ),
        )

        # ====================================================
        # TAMPER RESPONSE
        # ====================================================

        highlighted_path = (
            tamper_result.get(
                "highlighted_image_path"
            )
        )

        highlighted_image_url = None

        if highlighted_path:

            highlighted_image_url = (
                f"/tamper_outputs/"
                f"{Path(highlighted_path).name}"
            )

        tamper_evidence = {
            "suspicious_region_count": int(
                tamper_result.get(
                    "suspicious_region_count",
                    0,
                )
                or 0
            ),
            "suspicious_regions": (
                tamper_result.get(
                    "suspicious_regions",
                    [],
                )
            ),
            "highlighted_image_url": (
                highlighted_image_url
            ),
            "tamper_confidence": float(
                tamper_result.get(
                    "tamper_confidence",
                    0,
                )
                or 0
            ),
        }

        # ====================================================
        # EVIDENCE
        # ====================================================

        evidence = dict(
            risk.get(
                "evidence_breakdown",
                {},
            )
        )

        evidence[
            "tamper_confidence"
        ] = (
            tamper_evidence[
                "tamper_confidence"
            ]
        )

        evidence[
            "suspicious_region_count"
        ] = (
            tamper_evidence[
                "suspicious_region_count"
            ]
        )

        evidence[
            "visual_difference_percentage"
        ] = comparison[
            "difference_percentage"
        ]

        evidence[
            "reference_identity_match"
        ] = (
            best["identity_match"]
        )

        evidence[
            "reference_contextual_match"
        ] = (
            best["contextual_match"]
        )

        # ----------------------------------------------------
        # QR evidence is intentionally informational in this
        # step. Risk scoring remains unchanged so the current
        # working risk behavior is preserved.
        # ----------------------------------------------------

        evidence[
            "qr_status"
        ] = qr_verification[
            "status"
        ]

        evidence[
            "qr_reference_match"
        ] = qr_verification[
            "reference_qr_match"
        ]

        evidence[
            "qr_visible_number_match"
        ] = qr_verification[
            "visible_number_qr_match"
        ]

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {
            "document_id": document_id,
            "expected_document_type": (
                selected_type
            ),
            "uploaded_document_type": (
                submitted_document_type
            ),
            "document_type_match": True,
            "document_type_detection": {
                "reference": (
                    reference_type_result
                ),
                "submitted": (
                    submitted_type_result
                ),
            },
            "decision": (
                risk["classification"]
            ),
            "risk_score": (
                risk["risk_score"]
            ),
            "similarity_score": (
                comparison[
                    "similarity_score"
                ]
            ),
            "difference_percentage": (
                comparison[
                    "difference_percentage"
                ]
            ),
            "visual_integrity": {
                "score": comparison[
                    "visual_integrity_score"
                ],
                "similarity_score": comparison[
                    "similarity_score"
                ],
                "difference_percentage": comparison[
                    "difference_percentage"
                ],
            },
            "message": (
                risk["message"]
            ),
            "ocr": {
                "reference": reference_ocr,
                "submitted": submitted_ocr,
            },
            "field_comparison": (
                field_comparison
            ),
            "qr_verification": (
                qr_verification
            ),
            "reference_match": (
                reference_match
            ),
            "tamper_evidence": (
                tamper_evidence
            ),
            "evidence_breakdown": (
                evidence
            ),
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )