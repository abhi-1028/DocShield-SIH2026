def calculate_risk(
    similarity_score: float,
    field_comparison: dict | None = None,
    tamper_evidence: dict | None = None,
):
    """
    Calculate an explainable document screening risk score.

    Evidence weights:
    - Visual difference: 40 points
    - OCR field mismatches: 40 points
    - Tamper evidence: 20 points

    The score represents screening risk, not proof of fraud.
    """

    field_comparison = field_comparison or {}
    tamper_evidence = tamper_evidence or {}

    # ---------------------------------------------------------
    # 1. Visual evidence (maximum 40 points)
    # ---------------------------------------------------------
    visual_risk = max(0.0, min(100.0, 100.0 - similarity_score))
    visual_points = visual_risk * 0.40

    # ---------------------------------------------------------
    # 2. OCR field mismatch evidence (maximum 40 points)
    # ---------------------------------------------------------
    total_fields = field_comparison.get("total_fields", 0)
    matched_fields = field_comparison.get("matched_fields", 0)

    if total_fields > 0:
        mismatch_percentage = (
            (total_fields - matched_fields) / total_fields
        ) * 100
    else:
        mismatch_percentage = 0.0

    field_points = mismatch_percentage * 0.40

    # ---------------------------------------------------------
    # 3. Tamper evidence (maximum 20 points)
    # ---------------------------------------------------------
    suspicious_region_count = tamper_evidence.get(
        "suspicious_region_count",
        0
    )

    # Cap the contribution so many regions cannot dominate
    tamper_points = min(suspicious_region_count, 10) * 2.0

    # ---------------------------------------------------------
    # 4. Final evidence-fusion score
    # ---------------------------------------------------------
    risk_score = min(
        100.0,
        visual_points + field_points + tamper_points
    )

    # ---------------------------------------------------------
    # 5. Explainable classification
    # ---------------------------------------------------------
    if risk_score < 15:
        classification = "CLEAR"
        message = (
            "Document appears consistent with the reference "
            "with no significant screening indicators."
        )

    elif risk_score < 40:
        classification = "MANUAL REVIEW"
        message = (
            "Some inconsistencies or suspicious indicators were "
            "detected. Human verification is recommended."
        )

    else:
        classification = "HIGH RISK"
        message = (
            "Multiple or significant screening indicators were "
            "detected. Further verification is required."
        )

    return {
        "risk_score": round(risk_score, 2),
        "classification": classification,
        "message": message,

        "evidence_breakdown": {
            "visual_risk_points": round(visual_points, 2),
            "field_mismatch_points": round(field_points, 2),
            "tamper_points": round(tamper_points, 2),
            "visual_difference_percentage": round(
                visual_risk,
                2
            ),
            "field_mismatch_percentage": round(
                mismatch_percentage,
                2
            ),
            "suspicious_region_count": suspicious_region_count,
        }
    }