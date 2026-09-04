def calculate_risk(similarity_score: float):
    """
    Convert document comparison results into
    an explainable risk classification.
    """

    risk_score = 100 - similarity_score

    if risk_score < 15:
        classification = "CLEAR"
        message = (
            "Document appears consistent with the reference."
        )

    elif risk_score < 40:
        classification = "MANUAL REVIEW"
        message = (
            "Some inconsistencies were detected. "
            "Human verification is recommended."
        )

    else:
        classification = "HIGH RISK"
        message = (
            "Significant inconsistencies were detected."
        )

    return {
        "risk_score": round(risk_score, 2),
        "classification": classification,
        "message": message
    }