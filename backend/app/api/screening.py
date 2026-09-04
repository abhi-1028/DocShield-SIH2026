from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.comparison import compare_documents
from app.services.risk_engine import calculate_risk
from app.services.tamper_detection import detect_tampered_regions


router = APIRouter(
    prefix="/api",
    tags=["Document Screening"]
)


UPLOAD_DIR = Path("uploads")
REFERENCE_DIR = Path("reference_documents")
TAMPER_OUTPUT_DIR = Path("tamper_outputs")


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
        # Compare uploaded document with reference
        comparison = compare_documents(
            str(reference_file),
            str(uploaded_file)
        )

        # Calculate risk
        risk = calculate_risk(
            comparison["similarity_score"]
        )

        # Detect suspicious/tampered regions
        tamper_result = detect_tampered_regions(
            reference_path=str(reference_file),
            uploaded_path=str(uploaded_file),
            output_directory=str(TAMPER_OUTPUT_DIR)
        )

        # Return complete screening result
        return {
            "document_id": document_id,
            "decision": risk["decision"],
            "risk_score": risk["risk_score"],
            "similarity_score": comparison["similarity_score"],
            "difference_percentage": comparison["difference_percentage"],
            "message": risk["message"],

            "tamper_evidence": {
                "suspicious_region_count":
                    tamper_result["suspicious_region_count"],

                "suspicious_regions":
                    tamper_result["suspicious_regions"],

                "highlighted_image_path":
                    tamper_result["highlighted_image_path"]
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

