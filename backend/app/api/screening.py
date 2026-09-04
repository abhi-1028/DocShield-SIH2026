from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.comparison import compare_documents
from app.services.ocr import extract_text
from app.services.risk_engine import calculate_risk
from app.services.tamper_detection import detect_tampered_regions
from app.services.fields import extract_fields, compare_fields


router = APIRouter(prefix="/api", tags=["Document Screening"])


# Project directories
BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "uploads"
REFERENCE_DIR = BACKEND_DIR / "reference_documents"
TAMPER_OUTPUT_DIR = BACKEND_DIR / "tamper_outputs"


@router.post("/screen/{document_id}")
def screen_document(document_id: str):

    # ---------------------------------------------------------
    # 1. Find uploaded document
    # ---------------------------------------------------------
    uploaded_file = None

    if UPLOAD_DIR.exists():
        for file in UPLOAD_DIR.iterdir():
            if file.stem == document_id:
                uploaded_file = file
                break

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # ---------------------------------------------------------
    # 2. Find reference document
    # ---------------------------------------------------------
    reference_file = REFERENCE_DIR / "reference.jpeg"

    if not reference_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Reference document not found"
        )

    try:

        # -----------------------------------------------------
        # 3. OCR extraction
        # -----------------------------------------------------
        reference_ocr = extract_text(str(reference_file))
        submitted_ocr = extract_text(str(uploaded_file))

        # -----------------------------------------------------
        # 4. Extract structured fields
        # -----------------------------------------------------
        reference_fields = extract_fields(
            reference_ocr["text"]
        )

        submitted_fields = extract_fields(
            submitted_ocr["text"]
        )

        # -----------------------------------------------------
        # 5. Validate uploaded document
        # -----------------------------------------------------
        submitted_field_count = sum(
            1
            for value in submitted_fields.values()
            if value is not None
            and str(value).strip() != ""
        )

        # If the image does not contain enough recognizable
        # document fields, stop before fraud analysis.
        if submitted_field_count < 2:

            return {
                "document_id": document_id,
                "decision": "INVALID DOCUMENT",
                "risk_score": 0,
                "similarity_score": 0,
                "difference_percentage": 100,
                "message": (
                    "The uploaded image does not contain enough "
                    "recognizable document information for screening."
                ),
                "ocr": {
                    "reference": reference_ocr,
                    "submitted": submitted_ocr,
                },
                "field_comparison": {
                    "comparisons": {},
                    "mismatches": [],
                    "matched_fields": 0,
                    "total_fields": 0,
                    "match_percentage": 0,
                },
                "tamper_evidence": {
                    "suspicious_region_count": 0,
                    "suspicious_regions": [],
                    "highlighted_image_url": None,
                },
                "evidence_breakdown": {
                    "visual_risk_points": 0,
                    "field_mismatch_points": 0,
                    "tamper_points": 0,
                    "visual_difference_percentage": 100,
                    "field_mismatch_percentage": 0,
                    "suspicious_region_count": 0,
                },
            }

        # -----------------------------------------------------
        # 6. Compare reference and submitted document
        # -----------------------------------------------------
        comparison = compare_documents(
            str(reference_file),
            str(uploaded_file)
        )

        # -----------------------------------------------------
        # 7. Compare extracted fields
        # -----------------------------------------------------
        field_comparison = compare_fields(
            reference_fields,
            submitted_fields
        )

        # -----------------------------------------------------
        # 8. Tamper detection
        # -----------------------------------------------------
        tamper_result = detect_tampered_regions(
            reference_path=str(reference_file),
            uploaded_path=str(uploaded_file),
            output_directory=str(TAMPER_OUTPUT_DIR)
        )

        # -----------------------------------------------------
        # 9. Calculate risk
        # -----------------------------------------------------
        risk = calculate_risk(
            similarity_score=comparison["similarity_score"],
            field_comparison=field_comparison,
            tamper_evidence=tamper_result
        )

        # -----------------------------------------------------
        # 10. Return complete screening result
        # -----------------------------------------------------
        return {
            "document_id": document_id,
            "decision": risk["classification"],
            "risk_score": risk["risk_score"],
            "similarity_score": comparison["similarity_score"],
            "difference_percentage": comparison["difference_percentage"],
            "message": risk["message"],
            "ocr": {
                "reference": reference_ocr,
                "submitted": submitted_ocr,
            },
            "field_comparison": field_comparison,
            "tamper_evidence": {
                "suspicious_region_count": tamper_result[
                    "suspicious_region_count"
                ],
                "suspicious_regions": tamper_result[
                    "suspicious_regions"
                ],
                "highlighted_image_url": (
                    f"/tamper_outputs/"
                    f"{Path(tamper_result['highlighted_image_path']).name}"
                ),
            },
            "evidence_breakdown": risk["evidence_breakdown"],
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )