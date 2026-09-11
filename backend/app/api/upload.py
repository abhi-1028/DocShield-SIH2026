import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, File, HTTPException, UploadFile


router = APIRouter(
    prefix="/api",
    tags=["Document Upload"],
)


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BACKEND_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

MAX_UPLOAD_SIZE = 10 * 1024 * 1024

MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

SUPPORTED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
}


# ============================================================
# IMAGE SIGNATURE VALIDATION
# ============================================================

def _has_valid_image_signature(
    file_path: Path,
    extension: str,
):
    """
    Perform a lightweight file-signature check before OpenCV
    decoding.

    This prevents files with misleading extensions from being
    accepted simply because their filename looks valid.
    """

    try:

        with open(
            file_path,
            "rb",
        ) as file:

            header = file.read(16)

    except OSError:

        return False

    if extension in {
        ".jpg",
        ".jpeg",
    }:

        # JPEG files begin with FF D8 FF.
        return (
            len(header) >= 3
            and header[0] == 0xFF
            and header[1] == 0xD8
            and header[2] == 0xFF
        )

    if extension == ".png":

        # Standard PNG signature.
        png_signature = (
            b"\x89PNG\r\n\x1a\n"
        )

        return header.startswith(
            png_signature
        )

    return False


# ============================================================
# UPLOAD ENDPOINT
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    file_path = None

    # --------------------------------------------------------
    # 1. Check filename
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    original_filename = Path(
        file.filename
    ).name

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    # --------------------------------------------------------
    # 2. Check extension
    # --------------------------------------------------------

    file_extension = Path(
        original_filename
    ).suffix.lower()

    if file_extension not in SUPPORTED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Please upload JPG, JPEG or PNG."
            ),
        )

    # --------------------------------------------------------
    # 3. Check declared content type
    #
    # The MIME type is treated as an additional validation
    # signal. The actual file contents are still validated
    # later with signature checking and OpenCV.
    # --------------------------------------------------------

    content_type = (
        file.content_type
        or ""
    ).lower().strip()

    if (
        content_type
        and content_type
        not in SUPPORTED_CONTENT_TYPES
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid content type. "
                "Please upload a valid JPG, JPEG or PNG image."
            ),
        )

    # --------------------------------------------------------
    # 4. Generate document ID
    # --------------------------------------------------------

    document_id = str(
        uuid.uuid4()
    )

    file_name = (
        f"{document_id}{file_extension}"
    )

    file_path = (
        UPLOAD_DIR / file_name
    )

    total_size = 0

    # --------------------------------------------------------
    # 5. Stream upload to disk with size protection
    #
    # The previous implementation loaded the complete file
    # into memory before checking its size.
    #
    # This implementation enforces the limit while reading.
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "wb",
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(
                    chunk
                )

                if total_size > MAX_UPLOAD_SIZE:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "File is too large. "
                            "Maximum size is 10 MB."
                        ),
                    )

                buffer.write(
                    chunk
                )

    except HTTPException:

        if file_path is not None:
            file_path.unlink(
                missing_ok=True
            )

        raise

    except OSError:

        if file_path is not None:
            file_path.unlink(
                missing_ok=True
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "The server could not save the uploaded file."
            ),
        )

    except Exception:

        if file_path is not None:
            file_path.unlink(
                missing_ok=True
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while "
                "processing the upload."
            ),
        )

    # --------------------------------------------------------
    # 6. Empty-file validation
    # --------------------------------------------------------

    if total_size == 0:

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    # --------------------------------------------------------
    # 7. Validate actual file signature
    # --------------------------------------------------------

    if not _has_valid_image_signature(
        file_path,
        file_extension,
    ):

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file does not contain a valid "
                "JPG, JPEG or PNG image signature."
            ),
        )

    # --------------------------------------------------------
    # 8. Decode with OpenCV
    #
    # This remains the authoritative image validation step.
    # --------------------------------------------------------

    image = cv2.imread(
        str(file_path)
    )

    if image is None:

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded image could not be decoded. "
                "Please upload a valid JPG, JPEG or PNG image."
            ),
        )

    # --------------------------------------------------------
    # 9. Validate dimensions
    # --------------------------------------------------------

    height, width = image.shape[:2]

    if (
        height < MIN_IMAGE_HEIGHT
        or width < MIN_IMAGE_WIDTH
    ):

        file_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded image is too small "
                "for document screening."
            ),
        )

    # --------------------------------------------------------
    # 10. Return successful upload
    #
    # Keep the existing response contract unchanged so the
    # frontend does not need modification.
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": (
            "Document uploaded successfully"
        ),
        "document_id": document_id,
        "original_filename": (
            file.filename
        ),
        "file_type": file_extension,
        "file_size": total_size,
    }