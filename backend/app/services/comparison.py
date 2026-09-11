from pathlib import Path

import cv2
import numpy as np


SUPPORTED_REFERENCE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def compare_documents(reference_path: str, uploaded_path: str):
    """
    Compare two document images using a normalized pixel-difference
    measure. The result is intentionally a screening signal, not proof
    that two documents belong to the same person.
    """

    reference = cv2.imread(reference_path)
    uploaded = cv2.imread(uploaded_path)

    if reference is None:
        raise ValueError("Reference document could not be loaded")

    if uploaded is None:
        raise ValueError("Uploaded document could not be loaded")

    reference_height, reference_width = reference.shape[:2]

    uploaded = cv2.resize(
        uploaded,
        (reference_width, reference_height),
        interpolation=cv2.INTER_AREA,
    )

    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    uploaded_gray = cv2.cvtColor(uploaded, cv2.COLOR_BGR2GRAY)

    # Reduce harmless compression/noise differences.
    reference_gray = cv2.GaussianBlur(reference_gray, (3, 3), 0)
    uploaded_gray = cv2.GaussianBlur(uploaded_gray, (3, 3), 0)

    difference = cv2.absdiff(reference_gray, uploaded_gray)

    # Mean normalized difference is more stable than simply counting
    # every non-zero pixel, which made ordinary JPEG differences look
    # much worse than they actually were.
    mean_difference = float(np.mean(difference))
    difference_percentage = min(
        100.0,
        (mean_difference / 255.0) * 100.0,
    )

    similarity_score = max(
        0.0,
        100.0 - difference_percentage,
    )

    return {
        "similarity_score": round(similarity_score, 2),
        "difference_percentage": round(difference_percentage, 2),
        "visual_integrity_score": round(similarity_score, 2),
    }


def list_reference_images(reference_dir: str | Path) -> list[Path]:
    """Return all supported reference images in deterministic order."""

    directory = Path(reference_dir)

    if not directory.exists():
        return []

    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_REFERENCE_EXTENSIONS
        ],
        key=lambda path: path.name.lower(),
    )
