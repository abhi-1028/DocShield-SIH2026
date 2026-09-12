import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const analysisSteps = [
  {
    title: "OCR Text Extraction",
    description: "Reading and structuring document text",
    icon: "01",
  },
  {
    title: "Reference Comparison",
    description: "Comparing against authorized reference",
    icon: "02",
  },
  {
    title: "Tamper Analysis",
    description: "Scanning for suspicious visual regions",
    icon: "03",
  },
  {
    title: "Document Rules",
    description: "Checking document type and field consistency",
    icon: "04",
  },
  {
    title: "Risk Assessment",
    description: "Calculating explainable screening risk",
    icon: "05",
  },
];

function ShieldLogo({ small = false }) {
  return (
    <div className={`brand-logo ${small ? "brand-logo-small" : ""}`}>
      <svg
        viewBox="0 0 64 64"
        aria-hidden="true"
        className="brand-logo-svg"
      >
        <path
          d="M32 5 53 13v16c0 14-8.7 24.8-21 30C19.7 53.8 11 43 11 29V13L32 5Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinejoin="round"
        />

        <path
          d="M23 20h13l6 6v17H23V20Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        <path
          d="M36 20v7h7M27 33h11M27 39h8"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path
        d="M24 31V9M24 9l-8 8M24 9l8 8"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M10 28v8a4 4 0 0 0 4 4h20a4 4 0 0 0 4-4v-8"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path
        d="M14 6h14l8 8v28H14V6Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinejoin="round"
      />

      <path
        d="M28 6v9h8M19 24h12M19 31h12"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <circle
        cx="21"
        cy="21"
        r="11"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      />

      <path
        d="m30 30 9 9"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CompareIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <rect
        x="7"
        y="10"
        width="15"
        height="28"
        rx="2"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      />

      <rect
        x="26"
        y="10"
        width="15"
        height="28"
        rx="2"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      />

      <path
        d="M16 18v12M12 22h8M35 18v12M31 26h8"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function FieldIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <rect
        x="8"
        y="8"
        width="32"
        height="32"
        rx="5"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      />

      <path
        d="M15 17h18M15 24h18M15 31h10"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path
        d="M24 6 43 40H5L24 6Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinejoin="round"
      />

      <path
        d="M24 17v11M24 34v1"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

function getRiskClass(decision) {
  if (decision === "CLEAR") return "clear";
  if (decision === "MANUAL REVIEW") return "review";
  if (decision === "HIGH RISK") return "high";
  if (decision === "INVALID DOCUMENT") return "invalid";
  if (decision === "NO DATA FOUND") return "review";
  return "review";
}

function formatDocumentType(type) {
  if (type === "PAN") return "PAN Card";
  if (type === "AADHAAR") return "Aadhaar Card";
  return "Unknown Document";
}

function getReferenceId(type) {
  if (type === "PAN") return "PAN-REF-001";
  if (type === "AADHAAR") return "AADHAAR-REF-001";
  return "REFERENCE-N/A";
}

function getEvidenceStatus(score, maxScore) {
  if (!maxScore || score <= 0) return "low";

  const percentage = (score / maxScore) * 100;

  if (percentage >= 70) return "high";
  if (percentage >= 30) return "medium";
  return "low";
}

function formatFieldName(name) {
  const labels = {
    name: "Name",
    dob: "Date of Birth",
    id_number: "Identity Number",
    gender: "Gender",
    aadhaar_number: "Aadhaar Number",
    pan_number: "PAN Number",
    address: "Address",
  };

  return (
    labels[name] ||
    String(name || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase())
  );
}

function getFieldStatus(comparison) {
  if (!comparison) return "not-extracted";

  const submitted =
    comparison.submitted ??
    comparison.submitted_normalized ??
    "";

  if (!submitted) return "not-extracted";

  if (
    comparison.match === true ||
    comparison.status === "match" ||
    comparison.match_reason === "exact_normalized_match"
  ) {
    return "match";
  }

  return "mismatch";
}

function getApiUrl(path) {
  if (!path) return "";

  if (
    path.startsWith("http://") ||
    path.startsWith("https://")
  ) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function App() {
  const [pageLoading, setPageLoading] = useState(true);

  const [submittedFile, setSubmittedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  const fileInputRef = useRef(null);
  const completionTimerRef = useRef(null);
  const pageLoaderTimerRef = useRef(null);

  /*
   * ----------------------------------------------------------
   * INITIAL PAGE LOADING
   * ----------------------------------------------------------
   */
  useEffect(() => {
    pageLoaderTimerRef.current = setTimeout(() => {
      setPageLoading(false);
    }, 1400);

    return () => {
      if (pageLoaderTimerRef.current) {
        clearTimeout(pageLoaderTimerRef.current);
      }
    };
  }, []);

  /*
   * ----------------------------------------------------------
   * LIVE ANALYSIS STEP ANIMATION
   * ----------------------------------------------------------
   *
   * Steps 1-4 advance automatically.
   *
   * Step 5 is deliberately held until the actual backend
   * screening request has completed.
   *
   * This prevents Risk Assessment from appearing as if it is
   * completing early or being artificially extended.
   */
  useEffect(() => {
    if (!isAnalyzing) return;

    const interval = setInterval(() => {
      setCurrentStep((previousStep) => {
        /*
         * Stop automatic advancement at the final step.
         *
         * The final step is released by handleAnalyze()
         * when the backend response actually arrives.
         */
        if (previousStep >= analysisSteps.length - 1) {
          return previousStep;
        }

        /*
         * Advance normally through stages 1-4.
         */
        return previousStep + 1;
      });
    }, 650);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  /*
   * ----------------------------------------------------------
   * CLEANUP
   * ----------------------------------------------------------
   */
  useEffect(() => {
    return () => {
      if (completionTimerRef.current) {
        clearTimeout(completionTimerRef.current);
      }

      if (pageLoaderTimerRef.current) {
        clearTimeout(pageLoaderTimerRef.current);
      }
    };
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setAnalysisError("");

    const allowedTypes = ["image/png", "image/jpeg"];
    const maxSize = 10 * 1024 * 1024;

    if (!allowedTypes.includes(file.type)) {
      setAnalysisError(
        "Please upload a PNG or JPEG document image."
      );
      return;
    }

    if (file.size > maxSize) {
      setAnalysisError(
        "File size must be less than 10 MB."
      );
      return;
    }

    setSubmittedFile(file);
    setAnalysisResult(null);
    setAnalysisComplete(false);
    setShowResults(false);
    setCurrentStep(0);
  };

  const handleAnalyze = async () => {
    if (!submittedFile || isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisComplete(false);
    setShowResults(false);
    setAnalysisResult(null);
    setAnalysisError("");
    setCurrentStep(0);

    try {
      const formData = new FormData();
      formData.append("file", submittedFile);

      const uploadResponse = await fetch(
        `${API_BASE_URL}/api/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!uploadResponse.ok) {
        throw new Error("Document upload failed.");
      }

      const uploadData = await uploadResponse.json();

      const documentId =
        uploadData.document_id ||
        uploadData.id ||
        uploadData.filename;

      if (!documentId) {
        throw new Error(
          "The backend did not return a document ID."
        );
      }

      const screenResponse = await fetch(
        `${API_BASE_URL}/api/screen/${documentId}`,
        {
          method: "POST",
        }
      );

      if (!screenResponse.ok) {
        const errorText = await screenResponse.text();

        throw new Error(
          errorText || "Document screening failed."
        );
      }

      const result = await screenResponse.json();

      setAnalysisResult(result);

      /*
       * Backend processing has now actually completed.
       *
       * Only now do we mark the final Risk Assessment stage
       * complete.
       */
      setCurrentStep(analysisSteps.length - 1);

      completionTimerRef.current = setTimeout(() => {
        setIsAnalyzing(false);
        setAnalysisComplete(true);
      }, 650);
    } catch (error) {
      setIsAnalyzing(false);
      setAnalysisComplete(false);

      setAnalysisError(
        error?.message ||
          "Something went wrong while analyzing the document."
      );
    }
  };

  const handleReset = () => {
    if (completionTimerRef.current) {
      clearTimeout(completionTimerRef.current);
    }

    setSubmittedFile(null);
    setIsAnalyzing(false);
    setCurrentStep(0);
    setAnalysisComplete(false);
    setShowResults(false);
    setAnalysisResult(null);
    setAnalysisError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const riskClass = analysisResult
    ? getRiskClass(analysisResult.decision)
    : "";

  const detectedDocumentType =
    analysisResult?.uploaded_document_type ||
    analysisResult?.expected_document_type ||
    "UNKNOWN";

  const documentTypeLabel =
    formatDocumentType(detectedDocumentType);

  const referenceDocumentType =
    analysisResult?.expected_document_type ||
    detectedDocumentType ||
    "UNKNOWN";

  const referenceDocumentTypeLabel =
    formatDocumentType(referenceDocumentType);

  const referenceId =
    getReferenceId(referenceDocumentType);

  const isInvalidDocument =
    analysisResult?.decision === "INVALID DOCUMENT";

  const isNoDataFound =
    analysisResult?.decision === "NO DATA FOUND";

  const isTypeMismatch =
    analysisResult?.document_type_match === false &&
    !isInvalidDocument;

  const isFullScreeningResult =
    !isInvalidDocument &&
    !isTypeMismatch &&
    !isNoDataFound;

  const evidence =
    analysisResult?.evidence_breakdown || {};

  const tamperEvidence =
    analysisResult?.tamper_evidence || {};

  const suspiciousRegionCount = Number(
    tamperEvidence.suspicious_region_count ?? 0
  );

  const tamperConfidenceValue =
    tamperEvidence.tamper_confidence ??
    evidence.tamper_confidence ??
    0;

  const tamperConfidence = Math.max(
    0,
    Math.min(100, Number(tamperConfidenceValue) || 0)
  );

  const similarityScore = Number(
    analysisResult?.similarity_score ?? 0
  );

  const differencePercentage = Number(
    analysisResult?.difference_percentage ??
      evidence.visual_difference_percentage ??
      0
  );

  const fieldComparison =
    analysisResult?.field_comparison || {};

  const totalFields = Number(
    fieldComparison.total_fields ?? 0
  );

  const matchedFields = Number(
    fieldComparison.matched_fields ?? 0
  );

  const fieldMatchPercentage =
    totalFields > 0
      ? (matchedFields / totalFields) * 100
      : 0;

  const comparisons = Array.isArray(
    fieldComparison.comparisons
  )
    ? fieldComparison.comparisons
    : fieldComparison.comparisons
      ? Object.entries(fieldComparison.comparisons).map(
          ([field, value]) => ({
            field,
            ...value,
          })
        )
      : [];

  const highlightedImageUrl = getApiUrl(
    tamperEvidence.highlighted_image_url
  );

  const getDecisionTitle = () => {
    if (isInvalidDocument) {
      return "Document could not be validated";
    }

    if (isNoDataFound) {
      return "No reference data found";
    }

    if (isTypeMismatch) {
      return "Document type mismatch";
    }

    if (analysisResult?.decision === "CLEAR") {
      return "Document screening completed";
    }

    if (analysisResult?.decision === "MANUAL REVIEW") {
      return "Manual verification recommended";
    }

    return "High-risk indicators detected";
  };

  const getDecisionSubtitle = () => {
    if (isInvalidDocument) {
      return "The uploaded image did not contain enough recognizable document information for reliable screening.";
    }

    if (isNoDataFound) {
      return "No matching identity reference was found in the authorized reference repository.";
    }

    if (isTypeMismatch) {
      return "The uploaded document belongs to a different document type than the selected reference.";
    }

    if (analysisResult?.decision === "CLEAR") {
      return "The submitted document appears consistent with the authorized reference.";
    }

    if (analysisResult?.decision === "MANUAL REVIEW") {
      return "Some inconsistencies or suspicious indicators require human verification.";
    }

    return "Multiple or significant screening indicators require further verification.";
  };

  const getRecommendationTitle = () => {
    if (isInvalidDocument) {
      return "Upload a clearer document";
    }

    if (isNoDataFound) {
      return "Reference record unavailable";
    }

    if (isTypeMismatch) {
      return "Verify the document type";
    }

    if (analysisResult?.decision === "CLEAR") {
      return "Recommended action: proceed";
    }

    if (analysisResult?.decision === "MANUAL REVIEW") {
      return "Recommended action: manual verification";
    }

    return "Recommended action: further verification";
  };

  const getRecommendationText = () => {
    if (isInvalidDocument) {
      return "The system skipped fraud-risk scoring because the document could not be reliably recognized.";
    }

    if (isNoDataFound) {
      return "The submitted identity could not be matched to an authorized reference. The system skipped tamper and fraud-risk analysis.";
    }

    if (isTypeMismatch) {
      return "Document-type mismatch is treated as a verification issue, not as proof of tampering.";
    }

    if (analysisResult?.decision === "CLEAR") {
      return "No significant screening indicators were detected.";
    }

    if (analysisResult?.decision === "MANUAL REVIEW") {
      return "Review the highlighted evidence and OCR field comparison before making a final decision.";
    }

    return "Review the visual evidence, field mismatches, and suspicious regions before making a final decision.";
  };

  const renderEvidenceRow = (
    label,
    value,
    maxValue,
    suffix = "pts"
  ) => {
    const numericValue = Math.max(
      0,
      Number(value) || 0
    );

    const numericMax = Math.max(
      1,
      Number(maxValue) || 1
    );

    const percentage = Math.min(
      100,
      (numericValue / numericMax) * 100
    );

    return (
      <div className="evidence-row" key={label}>
        <div className="evidence-row-top">
          <span>{label}</span>

          <strong>
            {numericValue.toFixed(1)} /{" "}
            {numericMax.toFixed(0)} {suffix}
          </strong>
        </div>

        <div className="evidence-bar">
          <div
            className={`evidence-fill ${getEvidenceStatus(
              numericValue,
              numericMax
            )}`}
            style={{
              width: `${percentage}%`,
            }}
          />
        </div>
      </div>
    );
  };

  /*
   * ==========================================================
   * MAIN APPLICATION
   * ==========================================================
   */

  return (
    <div className="app-shell">

      {/* =====================================================
          INITIAL PAGE LOADING OVERLAY
          ===================================================== */}
      {pageLoading && (
        <div
          className={`page-loader ${
            pageLoading
              ? "page-loader-visible"
              : "page-loader-hidden"
          }`}
          aria-label="Loading DocShield"
        >
          <div className="page-loader-glow" />

          <div className="loader-brand">
            <div className="loader-shield">
              <ShieldLogo />
            </div>

            <div className="loader-brand-text">
              <h1>DocShield</h1>
              <p>AI-Assisted Document Screening</p>
            </div>
          </div>

          <div className="loader-progress">
            <div className="loader-progress-bar" />
          </div>

          <span className="loader-status">
            Initializing secure screening engine...
          </span>
        </div>
      )}

      {/* =====================================================
          RESULTS PAGE
          ===================================================== */}
      {showResults && analysisResult ? (
        <>
          <nav className="navbar">
            <div className="brand">
              <ShieldLogo />

              <div>
                <h2>DocShield</h2>
                <p>AI-Assisted Document Screening</p>
              </div>
            </div>

            <div className="nav-status">
              <span className="status-dot" />
              Screening Engine Online
            </div>
          </nav>

          <main className="results-page">
            <div className="results-topbar">
              <button
                className="back-btn"
                onClick={() => setShowResults(false)}
              >
                ← Back to Analysis
              </button>

              <span>SCREENING RESULT</span>
            </div>

            <section className={`result-hero ${riskClass}`}>
              <div>
                <span className="section-label">
                  {documentTypeLabel.toUpperCase()} SCREENING
                </span>

                <h1>{getDecisionTitle()}</h1>

                <p>{getDecisionSubtitle()}</p>
              </div>

              <div className={`risk-score-card ${riskClass}`}>
                <span>SCREENING RISK SCORE</span>

                <div className="risk-number">
                  <strong>
                    {Number(
                      analysisResult.risk_score ?? 0
                    ).toFixed(0)}
                  </strong>

                  <small>/100</small>
                </div>

                <div className="risk-label">
                  {analysisResult.decision}
                </div>
              </div>
            </section>

            <section
              className={`recommendation-banner ${riskClass}`}
            >
              <div className="recommendation-icon">
                {isInvalidDocument
                  ? "!"
                  : isTypeMismatch
                    ? "!"
                    : analysisResult.decision === "CLEAR"
                      ? "✓"
                      : "!"}
              </div>

              <div>
                <strong>
                  {getRecommendationTitle()}
                </strong>

                <p>{getRecommendationText()}</p>
              </div>
            </section>

            <section className="screening-metrics-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    KEY METRICS
                  </span>

                  <h2>Screening overview</h2>
                </div>
              </div>

              <div className="metrics-grid">
                <div className="metric-card">
                  <span>DOCUMENT TYPE</span>

                  <strong>{documentTypeLabel}</strong>

                  <small>
                    {isTypeMismatch
                      ? "Does not match expected type"
                      : "Detected document type"}
                  </small>
                </div>

                <div className="metric-card">
                  <span>VISUAL SIMILARITY</span>

                  <strong>
                    {similarityScore.toFixed(1)}%
                  </strong>

                  <small>
                    {differencePercentage.toFixed(1)}%
                    visual difference
                  </small>
                </div>

                <div className="metric-card">
                  <span>OCR FIELD MATCH</span>

                  <strong>
                    {fieldMatchPercentage.toFixed(0)}%
                  </strong>

                  <small>
                    {matchedFields} of {totalFields} fields
                    matched
                  </small>
                </div>

                <div className="metric-card">
                  <span>TAMPER CONFIDENCE</span>

                  <strong>
                    {isFullScreeningResult
                      ? `${tamperConfidence.toFixed(0)}%`
                      : "N/A"}
                  </strong>

                  <small>
                    {isFullScreeningResult
                      ? `${suspiciousRegionCount} suspicious region${
                          suspiciousRegionCount === 1
                            ? ""
                            : "s"
                        } detected`
                      : "Tamper analysis skipped"}
                  </small>
                </div>
              </div>
            </section>

            <section className="results-grid">
              <div className="result-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-label">
                      EVIDENCE BREAKDOWN
                    </span>

                    <h2>
                      Why this result was produced
                    </h2>
                  </div>

                  <div className="panel-total">
                    {Number(
                      analysisResult.risk_score ?? 0
                    ).toFixed(1)}{" "}
                    total points
                  </div>
                </div>

                <div className="evidence-list">
                  {isInvalidDocument || isNoDataFound ? (
                    <div className="evidence-empty">
                      <div>!</div>

                      <strong>
                        {isNoDataFound
                          ? "Reference matching unavailable"
                          : "Risk scoring was skipped"}
                      </strong>

                      <p>
                        {isNoDataFound
                          ? "No authorized reference record matched the submitted identity. Tamper and risk analysis were skipped."
                          : "The document did not contain enough recognizable information for reliable screening."}
                      </p>
                    </div>
                  ) : isTypeMismatch ? (
                    <>
                      {renderEvidenceRow(
                        "Document Type Mismatch",
                        evidence.document_type_points ?? 10,
                        10
                      )}

                      {renderEvidenceRow(
                        "Reference Comparison",
                        0,
                        40
                      )}

                      {renderEvidenceRow(
                        "OCR Field Analysis",
                        0,
                        30
                      )}

                      {renderEvidenceRow(
                        "Tamper Evidence",
                        0,
                        20
                      )}
                    </>
                  ) : (
                    <>
                      {renderEvidenceRow(
                        "Visual Difference",
                        evidence.visual_risk_points ?? 0,
                        40
                      )}

                      {renderEvidenceRow(
                        "OCR Field Mismatch",
                        evidence.field_mismatch_points ?? 0,
                        40
                      )}

                      {renderEvidenceRow(
                        "Tamper Evidence",
                        evidence.tamper_points ?? 0,
                        20
                      )}
                    </>
                  )}
                </div>
              </div>

              <div className="result-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-label">
                      DETECTED INDICATORS
                    </span>

                    <h2>Screening signals</h2>
                  </div>
                </div>

                <div className="indicator-list">
                  {isInvalidDocument ? (
                    <div className="indicator-item invalid">
                      <span>!</span>

                      <p>
                        Insufficient recognizable document
                        information. Fraud-risk scoring was
                        skipped.
                      </p>
                    </div>
                  ) : isTypeMismatch ? (
                    <>
                      <div className="indicator-item review">
                        <span>!</span>

                        <p>
                          Uploaded document detected as{" "}
                          <strong>
                            {documentTypeLabel}
                          </strong>
                          , while the expected reference is{" "}
                          <strong>
                            {referenceDocumentTypeLabel}
                          </strong>
                          .
                        </p>
                      </div>

                      <div className="indicator-item clear">
                        <span>✓</span>

                        <p>
                          Layout and tamper comparison were
                          skipped because document types do not
                          match.
                        </p>
                      </div>

                      <div className="indicator-item clear">
                        <span>✓</span>

                        <p>
                          Document-type mismatch is not treated
                          as evidence of tampering by itself.
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div
                        className={`indicator-item ${
                          matchedFields < totalFields
                            ? "review"
                            : "clear"
                        }`}
                      >
                        <span>
                          {matchedFields < totalFields
                            ? "!"
                            : "✓"}
                        </span>

                        <p>
                          {matchedFields} of {totalFields} OCR
                          fields matched the reference.
                        </p>
                      </div>

                      <div
                        className={`indicator-item ${
                          suspiciousRegionCount > 0
                            ? "high"
                            : "clear"
                        }`}
                      >
                        <span>
                          {suspiciousRegionCount > 0
                            ? "!"
                            : "✓"}
                        </span>

                        <p>
                          {suspiciousRegionCount > 0
                            ? `${suspiciousRegionCount} suspicious visual region${
                                suspiciousRegionCount === 1
                                  ? ""
                                  : "s"
                              } detected.`
                            : "No suspicious visual regions detected."}
                        </p>
                      </div>

                      <div className="indicator-item clear">
                        <span>✓</span>

                        <p>
                          Visual similarity score:
                          <strong>
                            {" "}
                            {similarityScore.toFixed(1)}%
                          </strong>
                          .
                        </p>
                      </div>

                      <div className="indicator-item clear">
                        <span>✓</span>

                        <p>
                          Tamper confidence:
                          <strong>
                            {" "}
                            {tamperConfidence.toFixed(0)}%
                          </strong>
                          .
                        </p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </section>

            {isFullScreeningResult && (
              <section className="result-panel tamper-confidence-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-label">
                      TAMPER ANALYSIS
                    </span>

                    <h2>
                      Visual integrity assessment
                    </h2>
                  </div>

                  <div className="panel-total">
                    {suspiciousRegionCount} regions
                  </div>
                </div>

                <div className="tamper-confidence-content">
                  <div className="tamper-confidence-score">
                    <strong>
                      {tamperConfidence.toFixed(0)}%
                    </strong>

                    <span>Tamper confidence</span>
                  </div>

                  <div className="tamper-confidence-details">
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{
                          width: `${tamperConfidence}%`,
                        }}
                      />
                    </div>

                    <div className="confidence-scale">
                      <span>Low</span>
                      <span>Moderate</span>
                      <span>High</span>
                    </div>

                    <p>
                      The score reflects the strength and
                      concentration of suspicious visual
                      differences detected during screening.
                      It is a screening indicator, not proof of
                      document fraud.
                    </p>
                  </div>
                </div>
              </section>
            )}

            <section className="result-panel field-comparison-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    OCR FIELD COMPARISON
                  </span>

                  <h2>Extracted document fields</h2>
                </div>

                <div className="comparison-badge">
                  {isFullScreeningResult
                    ? `${matchedFields}/${totalFields} matched`
                    : "Comparison skipped"}
                </div>
              </div>

              {isFullScreeningResult &&
              comparisons.length > 0 ? (
                <div className="comparison-table">
                  <div className="comparison-table-header">
                    <span>FIELD</span>
                    <span>REFERENCE</span>
                    <span>SUBMITTED</span>
                    <span>STATUS</span>
                  </div>

                  {comparisons.map((comparison, index) => {
                    const field =
                      comparison.field ||
                      comparison.name ||
                      Object.keys(comparison)[0] ||
                      `field_${index}`;

                    const status =
                      getFieldStatus(comparison);

                    return (
                      <div
                        className="comparison-table-row"
                        key={`${field}-${index}`}
                      >
                        <strong>
                          {formatFieldName(field)}
                        </strong>

                        <span>
                          {comparison.reference ||
                            comparison.reference_normalized ||
                            "—"}
                        </span>

                        <span>
                          {comparison.submitted ||
                            comparison.submitted_normalized ||
                            "—"}
                        </span>

                        <span
                          className={`field-status ${status}`}
                        >
                          {status === "match"
                            ? "MATCH"
                            : status === "not-extracted"
                              ? "NOT EXTRACTED"
                              : "MISMATCH"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="comparison-empty">
                  <strong>
                    Field comparison unavailable
                  </strong>

                  <p>
                    {isInvalidDocument
                      ? "The document was not recognized reliably."
                      : isTypeMismatch
                        ? "OCR field comparison was skipped because the document type does not match the expected reference."
                        : "No comparable OCR fields were returned by the screening engine."}
                  </p>
                </div>
              )}
            </section>

            {isFullScreeningResult && (
              <section className="result-panel visual-analysis-panel">
                <div className="panel-heading">
                  <div>
                    <span className="section-label">
                      VISUAL ANALYSIS
                    </span>

                    <h2>
                      Suspicious region visualization
                    </h2>
                  </div>

                  <div className="panel-total">
                    {suspiciousRegionCount} suspicious
                  </div>
                </div>

                {highlightedImageUrl ? (
                  <div className="tamper-image-container">
                    <img
                      src={highlightedImageUrl}
                      alt="Document with suspicious regions highlighted"
                      className="tamper-highlight-image"
                    />

                    <p className="visual-analysis-note">
                      Highlighted regions indicate areas where
                      the submitted document differs from the
                      authorized reference. These regions are
                      screening evidence and require human
                      verification.
                    </p>
                  </div>
                ) : (
                  <div className="no-tamper-result">
                    <div className="no-tamper-icon">
                      ✓
                    </div>

                    <div>
                      <strong>
                        No highlighted tamper regions
                      </strong>

                      <p>
                        The screening engine did not return a
                        highlighted suspicious-region image.
                      </p>
                    </div>
                  </div>
                )}
              </section>
            )}

            {isTypeMismatch && (
              <section className="result-panel mismatch-next-step">
                <div className="next-step-icon">!</div>

                <div>
                  <span className="section-label">
                    NEXT STEP
                  </span>

                  <h2>Verify the document type</h2>

                  <p>
                    The uploaded document was identified as{" "}
                    <strong>{documentTypeLabel}</strong>, while
                    the selected reference is{" "}
                    <strong>
                      {referenceDocumentTypeLabel}
                    </strong>
                    . Upload the expected document type or
                    select the appropriate screening workflow.
                  </p>
                </div>
              </section>
            )}

            {isInvalidDocument && (
              <section className="result-panel mismatch-next-step">
                <div className="next-step-icon">!</div>

                <div>
                  <span className="section-label">
                    NEXT STEP
                  </span>

                  <h2>Upload a clearer document</h2>

                  <p>
                    Make sure the full document is visible,
                    readable, and captured with sufficient
                    lighting and resolution.
                  </p>
                </div>
              </section>
            )}

            <section className="result-panel document-summary-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    SCREENING SUMMARY
                  </span>

                  <h2>Document details</h2>
                </div>
              </div>

              <div className="summary-grid">
                <div>
                  <span>DOCUMENT TYPE</span>

                  <strong>{documentTypeLabel}</strong>

                  <small>
                    Detected from OCR content
                  </small>
                </div>

                <div>
                  <span>REFERENCE</span>

                  <strong>{referenceId}</strong>

                  <small>
                    {referenceDocumentTypeLabel}
                  </small>
                </div>

                <div>
                  <span>SCREENING DECISION</span>

                  <strong
                    className={`${riskClass}-risk-text`}
                  >
                    {analysisResult.decision}
                  </strong>

                  <small>
                    Explainable screening outcome
                  </small>
                </div>

                <div>
                  <span>DOCUMENT ID</span>

                  <strong>
                    {analysisResult.document_id || "N/A"}
                  </strong>

                  <small>
                    Internal screening reference
                  </small>
                </div>
              </div>
            </section>

            <section className="results-disclaimer">
              <div className="shield">
                <ShieldLogo small />
              </div>

              <div>
                <h3>Screening disclaimer</h3>

                <p>
                  DocShield provides AI-assisted screening
                  indicators and does not establish fraud as a
                  fact. Final verification and decision-making
                  should be performed by an authorized human
                  reviewer.
                </p>
              </div>
            </section>

            <div className="results-actions">
              <button
                className="secondary-action-btn"
                onClick={handleReset}
              >
                Analyze Another Document
              </button>

              <button
                className="primary-action-btn"
                onClick={() => setShowResults(false)}
              >
                ← Return to Analysis
              </button>
            </div>
          </main>

          <footer>
            © 2026 DocShield · AI-assisted document screening
            prototype
          </footer>
        </>
      ) : (
        <>
          {/* =================================================
              MAIN ANALYSIS PAGE
              ================================================= */}
          <nav className="navbar">
            <div className="brand">
              <ShieldLogo />

              <div>
                <h2>DocShield</h2>
                <p>AI-Assisted Document Screening</p>
              </div>
            </div>

            <div className="nav-status">
              <span className="status-dot" />
              Screening Engine Online
            </div>
          </nav>

          <main>
            <section className="hero">
              <span className="hero-badge">
                <span className="hero-badge-dot" />
                AI-ASSISTED DOCUMENT SCREENING
              </span>

              <h1>
                Verify documents.
                <br />
                <span>Detect anomalies.</span>
              </h1>

              <p>
                DocShield compares submitted identity
                documents against authorized references using OCR,
                structured field comparison, visual analysis, and
                explainable risk scoring.
              </p>
            </section>

            <section className="workflow">
              {analysisSteps.map((step, index) => {
                const isActive =
                  isAnalyzing && index <= currentStep;

                const isComplete =
                  analysisComplete && index <= currentStep;

                return (
                  <div
                    className="step-wrapper"
                    key={step.title}
                  >
                    <div
                      className={`step ${
                        isActive || isComplete
                          ? "active"
                          : ""
                      }`}
                    >
                      <span>
                        {isComplete ? "✓" : index + 1}
                      </span>

                      {step.title}
                    </div>

                    {index < analysisSteps.length - 1 && (
                      <div
                        className={`line ${
                          (isAnalyzing &&
                            index < currentStep) ||
                          (analysisComplete &&
                            index < currentStep)
                            ? "active"
                            : ""
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </section>

            <section className="comparison-layout">
              <div className="reference-card">
                <div className="reference-header">
                  <div className="icon-box blue">
                    <DocumentIcon />
                  </div>

                  <div>
                    <span className="card-label">
                      AUTHORIZED SOURCE
                    </span>

                    <h3>Reference Document</h3>
                  </div>
                </div>

                <div className="reference-status">
                  <div className="status-check">✓</div>

                  <div>
                    <strong>
                      Authorized Reference
                    </strong>

                    <p>
                      Protected document repository
                    </p>
                  </div>
                </div>

                <div className="reference-details">
                  <div>
                    <span>DOCUMENT TYPE</span>

                    <strong>
                      {analysisResult
                        ? referenceDocumentTypeLabel
                        : "Auto-selected"}
                    </strong>
                  </div>

                  <div>
                    <span>REFERENCE ID</span>

                    <strong>
                      {analysisResult
                        ? referenceId
                        : "Pending Detection"}
                    </strong>
                  </div>

                  <div>
                    <span>HOLDER</span>

                    <strong>
                      {referenceDocumentType === "PAN"
                        ? "ARJUN SHARMA"
                        : "Verified Reference"}
                    </strong>
                  </div>

                  <div>
                    <span>STATUS</span>

                    <strong className="verified">
                      VERIFIED
                    </strong>
                  </div>
                </div>

                <div className="repository-note">
                  <span>🔒</span>
                  Managed inside the secure reference repository
                </div>
              </div>

              <div className="upload-card">
                <div className="card-top">
                  <div className="icon-box orange">
                    <UploadIcon />
                  </div>

                  <div>
                    <span className="card-label">
                      SUBMITTED DOCUMENT
                    </span>

                    <h3>Upload for Screening</h3>
                  </div>
                </div>

                <label
                  className={`upload-zone ${
                    submittedFile ? "has-file" : ""
                  } ${isAnalyzing ? "is-processing" : ""}`}
                  htmlFor="document-upload"
                >
                  <input
                    id="document-upload"
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg"
                    onChange={handleFileChange}
                    disabled={isAnalyzing}
                  />

                  <div className="upload-content">
                    <div className="upload-icon">
                      {submittedFile ? (
                        <div className="upload-success-icon">
                          ✓
                        </div>
                      ) : (
                        <UploadIcon />
                      )}
                    </div>

                    <h4>
                      {submittedFile
                        ? submittedFile.name
                        : "Click to upload document"}
                    </h4>

                    <p>
                      PNG or JPEG · Maximum 10 MB
                    </p>

                    {submittedFile && (
                      <div className="file-success">
                        ✓ Document ready for screening
                      </div>
                    )}
                  </div>
                </label>

                {analysisError && (
                  <div className="analysis-error">
                    <strong>Analysis error</strong>
                    <p>{analysisError}</p>
                  </div>
                )}
              </div>
            </section>

            <section className="pipeline">
              <div className="pipeline-heading">
                <span className="section-label">
                  SCREENING PIPELINE
                </span>

                <h2>
                  Multi-layer document{" "}
                  <span>analysis</span>
                </h2>

                <p>
                  Every document passes through multiple
                  independent screening stages before a risk score
                  is generated.
                </p>
              </div>

              <div className="pipeline-flow">
                <div className="pipeline-item">
                  <div>
                    <SearchIcon />
                  </div>

                  <strong>OCR</strong>
                  <span>Text Extraction</span>
                </div>

                <div className="pipeline-arrow">→</div>

                <div className="pipeline-item">
                  <div>
                    <CompareIcon />
                  </div>

                  <strong>Compare</strong>
                  <span>Reference Analysis</span>
                </div>

                <div className="pipeline-arrow">→</div>

                <div className="pipeline-item">
                  <div>
                    <FieldIcon />
                  </div>

                  <strong>Fields</strong>
                  <span>Data Validation</span>
                </div>

                <div className="pipeline-arrow">→</div>

                <div className="pipeline-item">
                  <div>
                    <WarningIcon />
                  </div>

                  <strong>Tamper</strong>
                  <span>Visual Analysis</span>
                </div>

                <div className="pipeline-arrow">→</div>

                <div className="pipeline-item final">
                  <div>
                    <ShieldLogo small />
                  </div>

                  <strong>Risk</strong>
                  <span>Final Assessment</span>
                </div>
              </div>
            </section>

            {/* =================================================
                LIVE ANALYSIS
                ================================================= */}
            {isAnalyzing && (
              <section className="analysis-panel">
                <div className="analysis-header">
                  <div>
                    <span className="section-label">
                      LIVE ANALYSIS
                    </span>

                    <h2>Screening document</h2>

                    <p>
                      Multiple verification layers are being
                      evaluated.
                    </p>
                  </div>

                  <div className="analysis-spinner">
                    <div className="analysis-spinner-ring">
                      <ShieldLogo small />
                    </div>

                    <span>AI</span>
                  </div>
                </div>

                <div className="analysis-steps">
                  {analysisSteps.map((step, index) => {
                    const isCurrent =
                      index === currentStep;

                    const isComplete =
                      index < currentStep;

                    return (
                      <div
                        className={`analysis-step ${
                          isCurrent ? "current" : ""
                        } ${
                          isComplete ? "complete" : ""
                        }`}
                        key={step.title}
                      >
                        <div className="analysis-step-icon">
                          {isComplete
                            ? "✓"
                            : step.icon}
                        </div>

                        <div className="analysis-step-content">
                          <strong>{step.title}</strong>

                          <span>
                            {isCurrent
                              ? "Processing..."
                              : step.description}
                          </span>
                        </div>

                        <div className="analysis-step-status">
                          {isCurrent ? (
                            <div className="mini-spinner" />
                          ) : isComplete ? (
                            "✓"
                          ) : (
                            "—"
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="analysis-progress">
                  <div
                    className="analysis-progress-bar"
                    style={{
                      /*
                       * Never show 100% while analysis is active.
                       *
                       * Step 5 therefore visually stays at 80%
                       * until the real backend response arrives.
                       */
                      width: `${
                        isAnalyzing
                          ? Math.min(
                              97,
                              ((currentStep + 1) /
                                analysisSteps.length) *
                                100
                            )
                          : 0
                      }%`,
                    }}
                  />
                </div>

                <div className="analysis-progress-meta">
                  <span>
                    Stage {currentStep + 1} of{" "}
                    {analysisSteps.length}
                  </span>

                  <span>
                    {isAnalyzing
                      ? Math.min(
                          97,
                          Math.round(
                            ((currentStep + 1) /
                              analysisSteps.length) *
                              100
                          )
                        )
                      : 0}
                    %
                  </span>
                </div>

                <p className="analysis-note">
                  <span>●</span>
                  Do not close this window while analysis is in
                  progress.
                </p>
              </section>
            )}

            {/* =================================================
                ANALYSIS COMPLETE
                ================================================= */}
            {analysisComplete && analysisResult && (
              <section className="analysis-complete">
                <div className="complete-icon">
                  <span>✓</span>
                </div>

                <div>
                  <span className="section-label">
                    ANALYSIS COMPLETE
                  </span>

                  <h2>Screening result is ready</h2>

                  <p>
                    Document analysis has completed successfully.
                  </p>
                </div>

                <button
                  className="view-results-btn"
                  onClick={() => setShowResults(true)}
                >
                  View Results
                  <span>→</span>
                </button>
              </section>
            )}

            <section className="analyze-section">
              <button
                className={`analyze-btn ${
                  submittedFile && !isAnalyzing
                    ? "enabled"
                    : ""
                }`}
                disabled={!submittedFile || isAnalyzing}
                onClick={handleAnalyze}
              >
                {isAnalyzing ? (
                  <>
                    <span className="button-spinner" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    Analyze Document
                    <span>→</span>
                  </>
                )}
              </button>

              <p>
                Analysis includes OCR, reference comparison,
                field validation, tamper detection, and risk
                assessment.
              </p>
            </section>

            <div className="reset-container">
              {submittedFile && !isAnalyzing && (
                <button
                  className="reset-btn"
                  onClick={handleReset}
                >
                  Reset
                </button>
              )}
            </div>

            <section className="disclaimer">
              <div className="shield">
                <ShieldLogo small />
              </div>

              <div>
                <h3>Important screening notice</h3>

                <p>
                  DocShield is an AI-assisted screening
                  prototype. Results identify potential
                  inconsistencies and suspicious indicators but do
                  not establish fraud as a fact. Final decisions
                  require authorized human verification.
                </p>
              </div>
            </section>
          </main>

          <footer>
            © 2026 DocShield · AI-assisted document screening
            prototype
          </footer>
        </>
      )}
    </div>
  );
}

export default App;