import cv2
import os
import uuid


def detect_tampered_regions(reference_path, uploaded_path, output_directory):
    """
    Compare a reference document with an uploaded document and
    identify localized visually suspicious regions.

    Important:
    Large global differences between two different document layouts
    should NOT automatically be classified as tampering.
    """

    # ============================================================
    # LOAD IMAGES
    # ============================================================

    reference = cv2.imread(reference_path)
    uploaded = cv2.imread(uploaded_path)

    if reference is None:
        raise ValueError("Reference image could not be loaded.")

    if uploaded is None:
        raise ValueError("Uploaded image could not be loaded.")

    # ============================================================
    # RESIZE UPLOADED IMAGE
    # ============================================================

    uploaded = cv2.resize(
        uploaded,
        (reference.shape[1], reference.shape[0]),
        interpolation=cv2.INTER_AREA,
    )

    # ============================================================
    # IMAGE DIFFERENCE
    # ============================================================

    difference = cv2.absdiff(
        reference,
        uploaded,
    )

    gray_difference = cv2.cvtColor(
        difference,
        cv2.COLOR_BGR2GRAY,
    )

    blurred = cv2.GaussianBlur(
        gray_difference,
        (5, 5),
        0,
    )

    # ============================================================
    # GLOBAL DIFFERENCE
    # ============================================================

    # Used only as a visual-difference measurement.
    # It should NOT by itself create a tamper region.

    _, threshold = cv2.threshold(
        blurred,
        30,
        255,
        cv2.THRESH_BINARY,
    )

    # ============================================================
    # MORPHOLOGICAL CLEANUP
    # ============================================================

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5),
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_CLOSE,
        kernel,
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        kernel,
    )

    # ============================================================
    # FIND CONTOURS
    # ============================================================

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    highlighted_image = uploaded.copy()

    suspicious_regions = []

    image_height, image_width = threshold.shape

    total_image_area = float(
        image_width * image_height
    )

    # ============================================================
    # REGION FILTERING
    # ============================================================

    for contour in contours:

        area = cv2.contourArea(contour)

        # Ignore tiny noise.
        if area < 300:
            continue

        x, y, width, height = cv2.boundingRect(contour)

        region_area = float(width * height)

        region_ratio = (
            region_area / total_image_area
        )

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # Ignore regions covering most of the document.
        #
        # A huge region means the submitted document is visually
        # different from the reference, not necessarily tampered.
        # --------------------------------------------------------

        if region_ratio > 0.60:
            continue

        # Ignore extremely wide/tall border-like artifacts.
        if (
            width > image_width * 0.90
            and height < image_height * 0.15
        ):
            continue

        if (
            height > image_height * 0.90
            and width < image_width * 0.15
        ):
            continue

        # Ignore very thin edge artifacts.
        if width <= 10 or height <= 10:
            continue

        # --------------------------------------------------------
        # Store suspicious localized region.
        # --------------------------------------------------------

        suspicious_regions.append(
            {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
                "area": float(area),
            }
        )

        # --------------------------------------------------------
        # Draw bounding box.
        # --------------------------------------------------------

        cv2.rectangle(
            highlighted_image,
            (x, y),
            (x + width, y + height),
            (0, 0, 255),
            3,
        )

        # --------------------------------------------------------
        # Add label.
        # --------------------------------------------------------

        cv2.putText(
            highlighted_image,
            "SUSPICIOUS REGION",
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    # ============================================================
    # OUTPUT DIRECTORY
    # ============================================================

    os.makedirs(
        output_directory,
        exist_ok=True,
    )

    output_filename = (
        f"tamper_{uuid.uuid4().hex}.png"
    )

    output_path = os.path.join(
        output_directory,
        output_filename,
    )

    # ============================================================
    # SAVE HIGHLIGHTED IMAGE
    # ============================================================

    success = cv2.imwrite(
        output_path,
        highlighted_image,
    )

    if not success:
        raise ValueError(
            "Could not save highlighted tamper image."
        )

    # ============================================================
    # RETURN RESULT
    # ============================================================

    return {
        "suspicious_region_count": len(
            suspicious_regions
        ),
        "suspicious_regions": suspicious_regions,
        "highlighted_image_path": output_path,
    }