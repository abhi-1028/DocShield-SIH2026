from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.comparison import compare_documents
from app.services.ocr import extract_text
from app.services.risk_engine import calculate_risk
from app.services.tamper_detection import detect_tampered_regions
from app.services.rules import extract_fields, compare_fields

router = APIRouter(
    prefix="/api",
    tags=["Document Screening"]
)


# Resolve paths relative to the backend directory,
# regardless of where Uvicorn is launched from.
BACKEND_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BACKEND_DIR / "uploads"
REFERENCE_DIR = BACKEND_DIR / "reference_documents"
TAMPER_OUTPUT_DIR = BACKEND_DIR / "tamper_outputs"


@router.post("/screen/{document_id}")
def screen_document(document_id: str):

    uploaded_file = None

    # Find the uploaded document
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

    # Prototype reference document
    reference_file = REFERENCE_DIR / "reference.jpeg"

    if not reference_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Reference document not found"
        )

    try:
        # Compare uploaded file with reference
        comparison = compare_documents(
            str(reference_file),
            str(uploaded_file)
        )

        # OCR reference document
        reference_ocr = extract_text(
            str(reference_file)
        )

        # OCR submitted document
        submitted_ocr = extract_text(
            str(uploaded_file)
        )
                # Extract structured fields from OCR text
        reference_fields = extract_fields(
            reference_ocr["text"]
        )

        submitted_fields = extract_fields(
            submitted_ocr["text"]
        )

        # Compare extracted fields
        field_comparison = compare_fields(
            reference_fields,
            submitted_fields
        )

        # Detect suspicious/tampered regions
        tamper_result = detect_tampered_regions(
            reference_path=str(reference_file),
            uploaded_path=str(uploaded_file),
            output_directory=str(TAMPER_OUTPUT_DIR)
        )

        # Calculate current risk
        risk = calculate_risk(
                similarity_score=comparison["similarity_score"],
                field_comparison=field_comparison,
                tamper_evidence=tamper_result
                )

        # Return complete screening result
        return {
            "document_id": document_id,

            "decision": risk["classification"],
"risk_score": risk["risk_score"],
"similarity_score": comparison["similarity_score"],
"difference_percentage": comparison["difference_percentage"],
"message": risk["message"],

"evidence_breakdown": risk["evidence_breakdown"],

            "ocr": {
        "reference": reference_ocr,
        "submitted": submitted_ocr
},
        "field_comparison": field_comparison,

            "tamper_evidence": {
                "suspicious_region_count":
                    tamper_result["suspicious_region_count"],

                "suspicious_regions":
                    tamper_result["suspicious_regions"],

                "highlighted_image_url":
                    f"/tamper_outputs/{Path(tamper_result['highlighted_image_path']).name}"
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )