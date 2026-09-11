def calculate_risk(
    similarity_score: float,
    field_comparison: dict | None = None,
    tamper_evidence: dict | None = None,
):
    """
    Explainable document screening risk score.

    Evidence weights:
    - Visual difference: up to 40 points
    - OCR field mismatches: up to 40 points
    - Tamper evidence: up to 20 points

    Additional:
    - Document type mismatch: up to 10 points
    - Tamper confidence refines the tamper contribution.

    Important behavior:
    - Any real field mismatch creates a minimum field-risk
      contribution of 20 points.
    - This prevents a critical document-field mismatch,
      such as a changed DOB, from being classified as CLEAR
      simply because only one of several fields differs.

    The score represents screening risk, not proof of fraud.
    """

    field_comparison = field_comparison or {}
    tamper_evidence = tamper_evidence or {}

    # ========================================================
    # VISUAL RISK
    # ========================================================

    try:
        similarity_score = float(
            similarity_score
        )
    except (
        TypeError,
        ValueError,
    ):
        similarity_score = 0.0

    similarity_score = max(
        0.0,
        min(
            100.0,
            similarity_score,
        ),
    )

    visual_risk = (
        100.0
        - similarity_score
    )

    visual_risk = max(
        0.0,
        min(
            100.0,
            visual_risk,
        ),
    )

    visual_points = (
        visual_risk
        * 0.40
    )

    # ========================================================
    # FIELD MISMATCH
    # ========================================================

    total_fields = field_comparison.get(
        "total_fields",
        0,
    )

    matched_fields = field_comparison.get(
        "matched_fields",
        0,
    )

    try:
        total_fields = int(
            total_fields
        )
    except (
        TypeError,
        ValueError,
    ):
        total_fields = 0

    try:
        matched_fields = int(
            matched_fields
        )
    except (
        TypeError,
        ValueError,
    ):
        matched_fields = 0

    total_fields = max(
        0,
        total_fields,
    )

    matched_fields = max(
        0,
        min(
            matched_fields,
            total_fields,
        ),
    )

    if total_fields > 0:

        mismatch_percentage = (
            (
                total_fields
                - matched_fields
            )
            / total_fields
        ) * 100.0

    else:

        mismatch_percentage = 0.0

    raw_field_points = (
        mismatch_percentage
        * 0.40
    )

    # --------------------------------------------------------
    # Critical mismatch floor.
    #
    # One wrong identity-related/document field should not
    # disappear inside a large number of otherwise matching
    # fields.
    # --------------------------------------------------------

    if mismatch_percentage > 0:

        field_points = max(
            20.0,
            raw_field_points,
        )

    else:

        field_points = 0.0

    field_points = min(
        40.0,
        field_points,
    )

    # ========================================================
    # TAMPER EVIDENCE
    # ========================================================

    suspicious_region_count = (
        tamper_evidence.get(
            "suspicious_region_count",
            0,
        )
    )

    try:
        suspicious_region_count = int(
            suspicious_region_count
        )
    except (
        TypeError,
        ValueError,
    ):
        suspicious_region_count = 0

    suspicious_region_count = max(
        0,
        suspicious_region_count,
    )

    region_points = (
        min(
            suspicious_region_count,
            10,
        )
        * 2.0
    )

    # ========================================================
    # TAMPER CONFIDENCE
    # ========================================================

    tamper_confidence = (
        tamper_evidence.get(
            "tamper_confidence",
            None,
        )
    )

    try:
        if tamper_confidence is not None:

            tamper_confidence = float(
                tamper_confidence
            )

    except (
        TypeError,
        ValueError,
    ):
        tamper_confidence = None

    if tamper_confidence is not None:

        tamper_confidence = max(
            0.0,
            min(
                100.0,
                tamper_confidence,
            ),
        )

        confidence_points = (
            tamper_confidence
            * 0.20
        )

        tamper_points = max(
            region_points,
            confidence_points,
        )

        tamper_points = min(
            20.0,
            tamper_points,
        )

    else:

        tamper_points = min(
            20.0,
            region_points,
        )

    # ========================================================
    # DOCUMENT TYPE
    # ========================================================

    reference_type = (
        field_comparison.get(
            "reference_document_type",
            "UNKNOWN",
        )
    )

    submitted_type = (
        field_comparison.get(
            "submitted_document_type",
            "UNKNOWN",
        )
    )

    reference_type = str(
        reference_type or "UNKNOWN"
    ).strip().upper()

    submitted_type = str(
        submitted_type or "UNKNOWN"
    ).strip().upper()

    document_type_mismatch = (
        reference_type != "UNKNOWN"
        and submitted_type != "UNKNOWN"
        and reference_type
        != submitted_type
    )

    document_type_points = (
        10.0
        if document_type_mismatch
        else 0.0
    )

    # ========================================================
    # TOTAL RISK
    # ========================================================

    risk_score = min(
        100.0,
        visual_points
        + field_points
        + tamper_points
        + document_type_points,
    )

    risk_score = max(
        0.0,
        risk_score,
    )

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    if document_type_mismatch:

        classification = (
            "MANUAL REVIEW"
        )

        message = (
            "The uploaded document does not "
            "match the expected document type. "
            "Manual verification is recommended."
        )

    elif risk_score < 15:

        classification = (
            "CLEAR"
        )

        message = (
            "Document appears consistent "
            "with the reference with no "
            "significant screening indicators."
        )

    elif risk_score < 40:

        classification = (
            "MANUAL REVIEW"
        )

        message = (
            "Some inconsistencies or suspicious "
            "indicators were detected. Human "
            "verification is recommended."
        )

    else:

        classification = (
            "HIGH RISK"
        )

        message = (
            "Multiple or significant screening "
            "indicators were detected. Further "
            "verification is required."
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "risk_score": round(
            risk_score,
            2,
        ),

        "classification": classification,

        "message": message,

        "evidence_breakdown": {

            # -------------------------------
            # VISUAL
            # -------------------------------

            "visual_risk_points": round(
                visual_points,
                2,
            ),

            "visual_difference_percentage": round(
                visual_risk,
                2,
            ),

            # -------------------------------
            # OCR FIELDS
            # -------------------------------

            "field_mismatch_points": round(
                field_points,
                2,
            ),

            "raw_field_mismatch_points": round(
                raw_field_points,
                2,
            ),

            "field_mismatch_percentage": round(
                mismatch_percentage,
                2,
            ),

            "total_fields": total_fields,

            "matched_fields": matched_fields,

            # -------------------------------
            # TAMPER
            # -------------------------------

            "tamper_points": round(
                tamper_points,
                2,
            ),

            "suspicious_region_count": (
                suspicious_region_count
            ),

            "tamper_confidence": (
                round(
                    tamper_confidence,
                    2,
                )
                if tamper_confidence
                is not None
                else None
            ),

            # -------------------------------
            # DOCUMENT TYPE
            # -------------------------------

            "document_type_points": round(
                document_type_points,
                2,
            ),

            "document_type_mismatch": (
                document_type_mismatch
            ),

            "reference_document_type": (
                reference_type
            ),

            "submitted_document_type": (
                submitted_type
            ),
        },
    }