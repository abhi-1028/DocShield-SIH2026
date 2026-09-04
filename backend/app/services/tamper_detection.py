import cv2
import os
import uuid


def detect_tampered_regions(reference_path, uploaded_path, output_directory):
    """
    Compare a reference document with an uploaded document
    and identify visually suspicious regions.
    """

    # Load images
    reference = cv2.imread(reference_path)
    uploaded = cv2.imread(uploaded_path)

    # Check whether images were loaded
    if reference is None:
        raise ValueError("Reference image could not be loaded.")

    if uploaded is None:
        raise ValueError("Uploaded image could not be loaded.")

    # Resize uploaded image to match reference
    uploaded = cv2.resize(
        uploaded,
        (reference.shape[1], reference.shape[0])
    )

    # Calculate absolute difference
    difference = cv2.absdiff(reference, uploaded)

    # Convert difference image to grayscale
    gray_difference = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY
    )

    # Blur slightly to reduce noise
    blurred = cv2.GaussianBlur(
        gray_difference,
        (5, 5),
        0
    )

    # Threshold the difference
    _, threshold = cv2.threshold(
        blurred,
        30,
        255,
        cv2.THRESH_BINARY
    )

    # Morphological operations to connect nearby changed pixels
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        kernel
    )

    threshold = cv2.dilate(
        threshold,
        kernel,
        iterations=1
    )

    # Find suspicious contours
    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # Copy uploaded image for highlighting
    highlighted_image = uploaded.copy()

    suspicious_regions = []

    # Filter and draw bounding boxes
    for contour in contours:

        area = cv2.contourArea(contour)

        # Ignore tiny noise regions
        if area < 300:
            continue

        x, y, width, height = cv2.boundingRect(contour)

        suspicious_regions.append({
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "area": float(area)
        })

        # Draw bounding box
        cv2.rectangle(
            highlighted_image,
            (x, y),
            (x + width, y + height),
            (0, 0, 255),
            3
        )

        # Add label
        cv2.putText(
            highlighted_image,
            "SUSPICIOUS REGION",
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2
        )

    # Create output directory if necessary
    os.makedirs(output_directory, exist_ok=True)

    # Generate unique output filename
    output_filename = f"tamper_{uuid.uuid4().hex}.png"

    output_path = os.path.join(
        output_directory,
        output_filename
    )

    # Save highlighted image
    cv2.imwrite(
        output_path,
        highlighted_image
    )

    return {
        "suspicious_region_count": len(suspicious_regions),
        "suspicious_regions": suspicious_regions,
        "highlighted_image_path": output_path
    }