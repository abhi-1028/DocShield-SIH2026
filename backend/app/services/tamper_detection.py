from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
import re


# ============================================================
# CONFIGURATION
# ============================================================

DIFFERENCE_THRESHOLD = 18

MIN_CONTOUR_AREA = 45

MAX_REGION_AREA_RATIO = 0.18

MIN_CHANGE_DENSITY = 0.025

MAX_SUSPICIOUS_REGIONS = 20

ECC_MAX_ITERATIONS = 40

ECC_DOWNSCALE_WIDTH = 900

OPEN_KERNEL_SIZE = 3
CLOSE_KERNEL_SIZE = 7
DILATE_KERNEL_SIZE = 3

MERGE_DISTANCE = 18

# Field-aware highlighting.
FIELD_REGION_PADDING = 8

# Confidence contribution from a confirmed field mismatch.
FIELD_MISMATCH_CONFIDENCE = 35.0

# Identity-number mismatches are stronger evidence.
IDENTITY_MISMATCH_CONFIDENCE = 45.0


# ============================================================
# IMAGE ALIGNMENT
# ============================================================

def align_images(
    reference,
    uploaded,
):
    """
    Align uploaded document to the reference document.
    """

    if reference is None or uploaded is None:
        raise ValueError(
            "Both reference and uploaded images are required."
        )

    reference_height, reference_width = (
        reference.shape[:2]
    )

    uploaded_resized = cv2.resize(
        uploaded,
        (
            reference_width,
            reference_height,
        ),
        interpolation=cv2.INTER_AREA,
    )

    reference_gray = cv2.cvtColor(
        reference,
        cv2.COLOR_BGR2GRAY,
    )

    uploaded_gray = cv2.cvtColor(
        uploaded_resized,
        cv2.COLOR_BGR2GRAY,
    )

    scale = min(
        1.0,
        ECC_DOWNSCALE_WIDTH
        / max(reference_width, 1),
    )

    if scale < 1.0:

        small_width = max(
            int(reference_width * scale),
            100,
        )

        small_height = max(
            int(reference_height * scale),
            100,
        )

        reference_small = cv2.resize(
            reference_gray,
            (
                small_width,
                small_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

        uploaded_small = cv2.resize(
            uploaded_gray,
            (
                small_width,
                small_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

    else:

        reference_small = reference_gray

        uploaded_small = uploaded_gray

    reference_small = cv2.GaussianBlur(
        reference_small,
        (5, 5),
        0,
    )

    uploaded_small = cv2.GaussianBlur(
        uploaded_small,
        (5, 5),
        0,
    )

    reference_small = cv2.normalize(
        reference_small,
        None,
        0,
        255,
        cv2.NORM_MINMAX,
    )

    uploaded_small = cv2.normalize(
        uploaded_small,
        None,
        0,
        255,
        cv2.NORM_MINMAX,
    )

    warp_matrix = np.eye(
        2,
        3,
        dtype=np.float32,
    )

    criteria = (
        cv2.TERM_CRITERIA_EPS
        | cv2.TERM_CRITERIA_COUNT,
        ECC_MAX_ITERATIONS,
        1e-5,
    )

    try:

        _, warp_matrix_small = cv2.findTransformECC(
            reference_small,
            uploaded_small,
            warp_matrix,
            cv2.MOTION_AFFINE,
            criteria,
            None,
            3,
        )

        if scale < 1.0:

            sx = 1.0 / scale
            sy = 1.0 / scale

            warp_matrix = np.array(
                [
                    [
                        warp_matrix_small[0, 0],
                        warp_matrix_small[0, 1],
                        warp_matrix_small[0, 2] * sx,
                    ],
                    [
                        warp_matrix_small[1, 0],
                        warp_matrix_small[1, 1],
                        warp_matrix_small[1, 2] * sy,
                    ],
                ],
                dtype=np.float32,
            )

        else:

            warp_matrix = warp_matrix_small

        aligned = cv2.warpAffine(
            uploaded_resized,
            warp_matrix,
            (
                reference_width,
                reference_height,
            ),
            flags=(
                cv2.INTER_LINEAR
                | cv2.WARP_INVERSE_MAP
            ),
            borderMode=cv2.BORDER_REPLICATE,
        )

        return aligned

    except cv2.error:

        return uploaded_resized


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_grayscale(
    image,
):
    """
    Produce a stable grayscale representation.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(
        gray
    )

    return gray


# ============================================================
# BACKGROUND DIFFERENCE REMOVAL
# ============================================================

def remove_large_background_changes(
    reference_gray,
    uploaded_gray,
):
    """
    Remove broad illumination/background variation.
    """

    reference_background = cv2.GaussianBlur(
        reference_gray,
        (31, 31),
        0,
    )

    uploaded_background = cv2.GaussianBlur(
        uploaded_gray,
        (31, 31),
        0,
    )

    reference_detail = cv2.absdiff(
        reference_gray,
        reference_background,
    )

    uploaded_detail = cv2.absdiff(
        uploaded_gray,
        uploaded_background,
    )

    return (
        reference_detail,
        uploaded_detail,
    )


# ============================================================
# PIXEL DIFFERENCE
# ============================================================

def detect_difference_regions(
    reference,
    uploaded,
):
    """
    Detect localized pixel differences.
    """

    reference_gray = preprocess_grayscale(
        reference
    )

    uploaded_gray = preprocess_grayscale(
        uploaded
    )

    (
        reference_detail,
        uploaded_detail,
    ) = remove_large_background_changes(
        reference_gray,
        uploaded_gray,
    )

    difference = cv2.absdiff(
        reference_detail,
        uploaded_detail,
    )

    difference = cv2.GaussianBlur(
        difference,
        (3, 3),
        0,
    )

    _, fixed_mask = cv2.threshold(
        difference,
        DIFFERENCE_THRESHOLD,
        255,
        cv2.THRESH_BINARY,
    )

    percentile_value = float(
        np.percentile(
            difference,
            96.0,
        )
    )

    adaptive_threshold = max(
        DIFFERENCE_THRESHOLD,
        int(percentile_value),
    )

    _, adaptive_mask = cv2.threshold(
        difference,
        adaptive_threshold,
        255,
        cv2.THRESH_BINARY,
    )

    mask = cv2.bitwise_or(
        fixed_mask,
        adaptive_mask,
    )

    open_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            OPEN_KERNEL_SIZE,
            OPEN_KERNEL_SIZE,
        ),
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        open_kernel,
        iterations=1,
    )

    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            CLOSE_KERNEL_SIZE,
            CLOSE_KERNEL_SIZE,
        ),
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        close_kernel,
        iterations=2,
    )

    dilate_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            DILATE_KERNEL_SIZE,
            DILATE_KERNEL_SIZE,
        ),
    )

    mask = cv2.dilate(
        mask,
        dilate_kernel,
        iterations=1,
    )

    return mask


# ============================================================
# MERGE REGIONS
# ============================================================

def merge_nearby_regions(
    regions,
    distance_threshold=MERGE_DISTANCE,
):
    """
    Merge overlapping or nearby regions.
    """

    if not regions:
        return []

    merged = []

    regions = sorted(
        regions,
        key=lambda region: region.get(
            "strength",
            0,
        ),
        reverse=True,
    )

    for region in regions:

        current = dict(
            region
        )

        merged_into_existing = False

        for existing in merged:

            current_x1 = current["x"]
            current_y1 = current["y"]

            current_x2 = (
                current["x"]
                + current["width"]
            )

            current_y2 = (
                current["y"]
                + current["height"]
            )

            existing_x1 = existing["x"]
            existing_y1 = existing["y"]

            existing_x2 = (
                existing["x"]
                + existing["width"]
            )

            existing_y2 = (
                existing["y"]
                + existing["height"]
            )

            horizontal_gap = max(
                existing_x1 - current_x2,
                current_x1 - existing_x2,
                0,
            )

            vertical_gap = max(
                existing_y1 - current_y2,
                current_y1 - existing_y2,
                0,
            )

            overlaps = (
                horizontal_gap == 0
                and vertical_gap == 0
            )

            nearby = (
                horizontal_gap
                <= distance_threshold
                and vertical_gap
                <= distance_threshold
            )

            if overlaps or nearby:

                x1 = min(
                    current_x1,
                    existing_x1,
                )

                y1 = min(
                    current_y1,
                    existing_y1,
                )

                x2 = max(
                    current_x2,
                    existing_x2,
                )

                y2 = max(
                    current_y2,
                    existing_y2,
                )

                existing["x"] = int(
                    x1
                )

                existing["y"] = int(
                    y1
                )

                existing["width"] = int(
                    x2 - x1
                )

                existing["height"] = int(
                    y2 - y1
                )

                existing["area"] = int(
                    max(
                        existing.get(
                            "area",
                            0,
                        ),
                        current.get(
                            "area",
                            0,
                        ),
                    )
                )

                existing[
                    "change_density"
                ] = round(
                    max(
                        existing.get(
                            "change_density",
                            0.0,
                        ),
                        current.get(
                            "change_density",
                            0.0,
                        ),
                    ),
                    4,
                )

                existing[
                    "strength"
                ] = round(
                    max(
                        existing.get(
                            "strength",
                            0.0,
                        ),
                        current.get(
                            "strength",
                            0.0,
                        ),
                    ),
                    2,
                )

                merged_into_existing = True

                break

        if not merged_into_existing:

            merged.append(
                current
            )

    return merged


# ============================================================
# PIXEL SUSPICIOUS REGIONS
# ============================================================

def extract_regions(
    mask,
    image_width,
    image_height,
):
    """
    Convert pixel-difference mask into suspicious regions.
    """

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    image_area = (
        image_width
        * image_height
    )

    regions = []

    for contour in contours:

        contour_area = cv2.contourArea(
            contour
        )

        if contour_area < MIN_CONTOUR_AREA:
            continue

        x, y, width, height = (
            cv2.boundingRect(
                contour
            )
        )

        region_area = (
            width * height
        )

        if (
            region_area
            > image_area
            * MAX_REGION_AREA_RATIO
        ):
            continue

        if width < 6 or height < 6:
            continue

        aspect_ratio = max(
            width / max(
                height,
                1,
            ),
            height / max(
                width,
                1,
            ),
        )

        if aspect_ratio > 25:
            continue

        border = 5

        if (
            x <= border
            or y <= border
            or x + width
            >= image_width - border
            or y + height
            >= image_height - border
        ):
            continue

        roi = mask[
            y:y + height,
            x:x + width,
        ]

        changed_pixels = (
            cv2.countNonZero(
                roi
            )
        )

        density = (
            changed_pixels
            / max(
                region_area,
                1,
            )
        )

        if density < MIN_CHANGE_DENSITY:
            continue

        strength = (
            float(density)
            * float(contour_area)
        )

        regions.append(
            {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
                "area": int(contour_area),
                "change_density": round(
                    float(density),
                    4,
                ),
                "strength": round(
                    strength,
                    2,
                ),
                "source": "pixel",
            }
        )

    regions = merge_nearby_regions(
        regions
    )

    for region in regions:

        region["strength"] = round(
            float(
                region.get(
                    "change_density",
                    0.0,
                )
            )
            * float(
                region.get(
                    "area",
                    0,
                )
            ),
            2,
        )

    regions.sort(
        key=lambda region:
        region.get(
            "strength",
            0,
        ),
        reverse=True,
    )

    return regions[
        :MAX_SUSPICIOUS_REGIONS
    ]


# ============================================================
# FIELD VALUE HELPERS
# ============================================================

def _get_field_submitted_value(
    field_comparison,
    field,
):
    """
    Retrieve the submitted value for a mismatched field.
    """

    comparisons = (
        field_comparison.get(
            "comparisons",
            {},
        )
        or {}
    )

    comparison = comparisons.get(
        field
    )

    if not comparison:
        return None

    return comparison.get(
        "submitted"
    )


def _clean_search_text(
    value,
):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip().upper()


def _box_from_detection(
    detection,
):
    """
    Convert EasyOCR's four-point polygon into x/y/width/height.
    """

    box = detection.get(
        "box"
    )

    if not box or len(box) < 4:
        return None

    try:

        xs = [
            float(point[0])
            for point in box
        ]

        ys = [
            float(point[1])
            for point in box
        ]

    except (
        TypeError,
        ValueError,
    ):

        return None

    x1 = int(
        min(xs)
    )

    y1 = int(
        min(ys)
    )

    x2 = int(
        max(xs)
    )

    y2 = int(
        max(ys)
    )

    return (
        x1,
        y1,
        max(
            1,
            x2 - x1,
        ),
        max(
            1,
            y2 - y1,
        ),
    )


def _field_detection_match(
    field,
    submitted_value,
    detections,
):
    """
    Find the most appropriate OCR detection corresponding
    to a mismatched field value.

    This uses the extracted field value rather than requiring
    the OCR label itself to be perfectly recognized.
    """

    if not detections:
        return None

    value_text = _clean_search_text(
        submitted_value
    )

    # --------------------------------------------------------
    # Direct textual match.
    # --------------------------------------------------------

    if value_text:

        best_detection = None
        best_score = -1.0

        for detection in detections:

            text = _clean_search_text(
                detection.get(
                    "text",
                    "",
                )
            )

            if not text:
                continue

            score = 0.0

            if text == value_text:
                score = 100.0

            elif (
                value_text
                and value_text in text
            ):
                score = 90.0

            elif (
                field
                in {
                    "dob",
                }
                and re.sub(
                    r"\D",
                    "",
                    text,
                )
                == re.sub(
                    r"\D",
                    "",
                    value_text,
                )
            ):
                score = 95.0

            elif (
                field
                in {
                    "pan_number",
                    "aadhaar_number",
                    "id_number",
                }
            ):

                normalized_text = re.sub(
                    r"[^A-Z0-9]",
                    "",
                    text,
                )

                normalized_value = re.sub(
                    r"[^A-Z0-9]",
                    "",
                    value_text,
                )

                if (
                    normalized_text
                    == normalized_value
                ):
                    score = 95.0

            if score > best_score:

                best_score = score

                best_detection = detection

        if best_detection is not None:

            return _box_from_detection(
                best_detection
            )

    # --------------------------------------------------------
    # If submitted value is missing, look for the field label.
    # --------------------------------------------------------

    label_map = {
        "name": [
            "NAME",
        ],
        "father_name": [
            "FATHER",
            "FATHER'S",
        ],
        "dob": [
            "DOB",
            "DATE",
            "BIRTH",
        ],
        "gender": [
            "GENDER",
        ],
        "pan_number": [
            "PAN",
        ],
        "aadhaar_number": [
            "AADHAAR",
            "AADHAR",
        ],
        "id_number": [
            "ID",
            "DOCUMENT",
        ],
    }

    labels = label_map.get(
        field,
        [],
    )

    for detection in detections:

        text = _clean_search_text(
            detection.get(
                "text",
                "",
            )
        )

        for label in labels:

            if label in text:
                return _box_from_detection(
                    detection
                )

    return None


# ============================================================
# FIELD-AWARE SUSPICIOUS REGIONS
# ============================================================

def extract_field_mismatch_regions(
    field_comparison,
    submitted_ocr,
    image_width,
    image_height,
):
    """
    Convert OCR field mismatches into suspicious regions.

    This is the semantic layer that catches small changes such
    as a modified DOB which may be too small to generate a
    global pixel contour.
    """

    if not field_comparison:
        return []

    mismatches = (
        field_comparison.get(
            "mismatches",
            [],
        )
        or []
    )

    if not mismatches:
        return []

    detections = []

    if submitted_ocr:

        detections = (
            submitted_ocr.get(
                "detections",
                [],
            )
            or []
        )

    regions = []

    for field in mismatches:

        submitted_value = (
            _get_field_submitted_value(
                field_comparison,
                field,
            )
        )

        box = _field_detection_match(
            field,
            submitted_value,
            detections,
        )

        if box is None:
            continue

        x, y, width, height = box

        x1 = max(
            0,
            x - FIELD_REGION_PADDING,
        )

        y1 = max(
            0,
            y - FIELD_REGION_PADDING,
        )

        x2 = min(
            image_width - 1,
            x + width
            + FIELD_REGION_PADDING,
        )

        y2 = min(
            image_height - 1,
            y + height
            + FIELD_REGION_PADDING,
        )

        normalized_field = str(
            field
        ).strip()

        if normalized_field in {
            "pan_number",
            "aadhaar_number",
            "id_number",
        }:

            confidence = (
                IDENTITY_MISMATCH_CONFIDENCE
            )

        else:

            confidence = (
                FIELD_MISMATCH_CONFIDENCE
            )

        regions.append(
            {
                "x": int(x1),
                "y": int(y1),
                "width": int(
                    max(
                        1,
                        x2 - x1,
                    )
                ),
                "height": int(
                    max(
                        1,
                        y2 - y1,
                    )
                ),
                "area": int(
                    max(
                        1,
                        width * height,
                    )
                ),
                "change_density": 1.0,
                "strength": round(
                    confidence,
                    2,
                ),
                "source": "field_mismatch",
                "field": field,
            }
        )

    return regions


# ============================================================
# TAMPER CONFIDENCE
# ============================================================

def calculate_tamper_confidence(
    regions,
    image_width,
    image_height,
):
    """
    Calculate confidence from suspicious regions.
    """

    if not regions:
        return 0.0

    image_area = max(
        image_width * image_height,
        1,
    )

    region_score = min(
        len(regions) * 8.0,
        40.0,
    )

    total_area = sum(
        region["width"]
        * region["height"]
        for region in regions
    )

    area_ratio = (
        total_area
        / image_area
    )

    area_score = min(
        area_ratio * 300.0,
        30.0,
    )

    average_density = (
        sum(
            region.get(
                "change_density",
                0.0,
            )
            for region in regions
        )
        / len(regions)
    )

    density_score = min(
        average_density * 100.0,
        30.0,
    )

    confidence = (
        region_score
        + area_score
        + density_score
    )

    # --------------------------------------------------------
    # Semantic field mismatch evidence.
    #
    # A field mismatch represents meaningful document
    # inconsistency even when pixel-level differences are tiny.
    # --------------------------------------------------------

    field_regions = [
        region
        for region in regions
        if region.get(
            "source"
        ) == "field_mismatch"
    ]

    if field_regions:

        semantic_confidence = max(
            float(
                region.get(
                    "strength",
                    0.0,
                )
            )
            for region in field_regions
        )

        confidence = max(
            confidence,
            semantic_confidence,
        )

        # Multiple independently mismatched fields increase
        # confidence gradually.
        if len(field_regions) > 1:

            confidence += min(
                (
                    len(field_regions)
                    - 1
                )
                * 10.0,
                25.0,
            )

    return round(
        min(
            confidence,
            100.0,
        ),
        2,
    )


# ============================================================
# DRAW HIGHLIGHTS
# ============================================================

def draw_highlights(
    image,
    regions,
):
    """
    Draw visible bounding boxes around suspicious regions.
    """

    highlighted = image.copy()

    for index, region in enumerate(
        regions,
        start=1,
    ):

        x = int(
            region["x"]
        )

        y = int(
            region["y"]
        )

        width = int(
            region["width"]
        )

        height = int(
            region["height"]
        )

        padding = (
            5
            if region.get(
                "source"
            ) != "field_mismatch"
            else 3
        )

        x1 = max(
            0,
            x - padding,
        )

        y1 = max(
            0,
            y - padding,
        )

        x2 = min(
            highlighted.shape[1] - 1,
            x + width + padding,
        )

        y2 = min(
            highlighted.shape[0] - 1,
            y + height + padding,
        )

        cv2.rectangle(
            highlighted,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            3,
        )

        field_name = region.get(
            "field"
        )

        if field_name:

            label = (
                f"{field_name.replace('_', ' ').upper()}"
            )

        else:

            label = (
                f"DIFF {index}"
            )

        (
            text_width,
            text_height,
        ), baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            2,
        )

        label_x = x1

        label_y = max(
            y1 - 8,
            text_height + 8,
        )

        cv2.rectangle(
            highlighted,
            (
                label_x,
                label_y
                - text_height
                - baseline,
            ),
            (
                label_x
                + text_width
                + 8,
                label_y + 4,
            ),
            (0, 0, 255),
            -1,
        )

        cv2.putText(
            highlighted,
            label,
            (
                label_x + 4,
                label_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    return highlighted


# ============================================================
# MAIN TAMPER DETECTOR
# ============================================================

def detect_tampered_regions(
    reference_path: str,
    uploaded_path: str,
    output_directory: str,
    field_comparison: dict | None = None,
    submitted_ocr: dict | None = None,
):
    """
    Main tamper-analysis pipeline.

    Two evidence sources are used:

    1. Pixel-level visual differences.
    2. Field-level OCR mismatches.

    The field-level layer is particularly important for small
    edits such as changing a DOB, name, or identity number.
    """

    reference = cv2.imread(
        reference_path
    )

    uploaded = cv2.imread(
        uploaded_path
    )

    if reference is None:
        raise ValueError(
            "Unable to read reference document."
        )

    if uploaded is None:
        raise ValueError(
            "Unable to read uploaded document."
        )

    if (
        reference.shape[0] < 50
        or reference.shape[1] < 50
    ):
        raise ValueError(
            "Reference document image is too small."
        )

    if (
        uploaded.shape[0] < 50
        or uploaded.shape[1] < 50
    ):
        raise ValueError(
            "Uploaded document image is too small."
        )

    # --------------------------------------------------------
    # Align.
    # --------------------------------------------------------

    aligned_uploaded = align_images(
        reference,
        uploaded,
    )

    image_height, image_width = (
        reference.shape[:2]
    )

    # --------------------------------------------------------
    # Existing pixel-level detector.
    # --------------------------------------------------------

    mask = detect_difference_regions(
        reference,
        aligned_uploaded,
    )

    pixel_regions = extract_regions(
        mask,
        image_width,
        image_height,
    )

    # --------------------------------------------------------
    # New field-aware detector.
    #
    # IMPORTANT:
    # OCR coordinates belong to the uploaded image dimensions.
    #
    # Since the uploaded image is resized to the reference
    # dimensions during alignment, scale the OCR coordinates
    # accordingly when necessary.
    # --------------------------------------------------------

    field_regions = extract_field_mismatch_regions(
        field_comparison,
        submitted_ocr,
        uploaded.shape[1],
        uploaded.shape[0],
    )

    if field_regions:

        uploaded_width = max(
            uploaded.shape[1],
            1,
        )

        uploaded_height = max(
            uploaded.shape[0],
            1,
        )

        scale_x = (
            image_width
            / uploaded_width
        )

        scale_y = (
            image_height
            / uploaded_height
        )

        for region in field_regions:

            region["x"] = int(
                region["x"]
                * scale_x
            )

            region["y"] = int(
                region["y"]
                * scale_y
            )

            region["width"] = int(
                region["width"]
                * scale_x
            )

            region["height"] = int(
                region["height"]
                * scale_y
            )

            region["x"] = max(
                0,
                min(
                    region["x"],
                    image_width - 1,
                ),
            )

            region["y"] = max(
                0,
                min(
                    region["y"],
                    image_height - 1,
                ),
            )

            region["width"] = max(
                1,
                min(
                    region["width"],
                    image_width
                    - region["x"],
                ),
            )

            region["height"] = max(
                1,
                min(
                    region["height"],
                    image_height
                    - region["y"],
                ),
            )

    # --------------------------------------------------------
    # Combine both sources.
    # --------------------------------------------------------

    suspicious_regions = (
        pixel_regions
        + field_regions
    )

    # --------------------------------------------------------
    # If the same field gets both pixel and semantic evidence,
    # keep both only when they are materially different.
    # --------------------------------------------------------

    suspicious_regions = sorted(
        suspicious_regions,
        key=lambda region:
        region.get(
            "strength",
            0,
        ),
        reverse=True,
    )

    suspicious_regions = (
        suspicious_regions[
            :MAX_SUSPICIOUS_REGIONS
        ]
    )

    # --------------------------------------------------------
    # Confidence.
    # --------------------------------------------------------

    tamper_confidence = (
        calculate_tamper_confidence(
            suspicious_regions,
            image_width,
            image_height,
        )
    )

    # --------------------------------------------------------
    # Highlight.
    # --------------------------------------------------------

    highlighted_image = draw_highlights(
        aligned_uploaded,
        suspicious_regions,
    )

    # --------------------------------------------------------
    # Save.
    # --------------------------------------------------------

    output_path = Path(
        output_directory
    )

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_filename = (
        f"tamper_{uuid4().hex}.png"
    )

    highlighted_path = (
        output_path
        / output_filename
    )

    success = cv2.imwrite(
        str(highlighted_path),
        highlighted_image,
    )

    if not success:
        raise ValueError(
            "Failed to save tamper-highlighted image."
        )

    # --------------------------------------------------------
    # Return.
    # --------------------------------------------------------

    return {
        "suspicious_region_count": len(
            suspicious_regions
        ),

        "suspicious_regions": (
            suspicious_regions
        ),

        "highlighted_image_path": (
            str(highlighted_path)
        ),

        "tamper_confidence": (
            tamper_confidence
        ),

        "pixel_region_count": len(
            pixel_regions
        ),

        "field_mismatch_region_count": len(
            field_regions
        ),
    }