import cv2
import numpy as np


def compare_documents(reference_path: str, uploaded_path: str):
    """
    Compare an uploaded document against a reference document.
    """

    reference = cv2.imread(reference_path)
    uploaded = cv2.imread(uploaded_path)

    if reference is None:
        raise ValueError("Reference document could not be loaded")

    if uploaded is None:
        raise ValueError("Uploaded document could not be loaded")

    # Resize uploaded image to match reference dimensions
    uploaded = cv2.resize(
        uploaded,
        (reference.shape[1], reference.shape[0])
    )

    # Calculate pixel difference
    difference = cv2.absdiff(reference, uploaded)

    # Convert difference image to grayscale
    gray_difference = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY
    )

    # Count changed pixels
    changed_pixels = np.count_nonzero(gray_difference)
    total_pixels = gray_difference.size

    difference_percentage = (
        changed_pixels / total_pixels
    ) * 100

    similarity_score = max(
        0,
        100 - difference_percentage
    )

    return {
        "similarity_score": round(float(similarity_score), 2),
        "difference_percentage": round(
            float(difference_percentage),
            2
        )
    }