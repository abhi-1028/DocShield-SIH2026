import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const analysisSteps = [
  {
    title: "OCR Text Extraction",
    description: "Extracting text and document fields",
    icon: "Aa",
  },
  {
    title: "Reference Comparison",
    description: "Comparing against authorized reference",
    icon: "◫",
  },
  {
    title: "Tamper Analysis",
    description: "Checking for visual anomalies",
    icon: "⚠",
  },
  {
    title: "Document Rules",
    description: "Validating format and field consistency",
    icon: "✓",
  },
  {
    title: "Risk Assessment",
    description: "Fusing evidence into screening result",
    icon: "◈",
  },
];

function getRiskClass(decision) {
  if (decision === "CLEAR") {
    return "clear";
  }

  if (decision === "MANUAL REVIEW") {
    return "review";
  }

  if (decision === "HIGH RISK") {
    return "high";
  }

  if (decision === "INVALID DOCUMENT") {
    return "invalid";
  }

  return "";
}

function getEvidenceStatus(score, maxScore) {
  if (!maxScore || maxScore <= 0) {
    return "low";
  }

  const percentage = (score / maxScore) * 100;

  if (percentage >= 70) {
    return "high";
  }

  if (percentage >= 30) {
    return "medium";
  }

  return "low";
}

function formatFieldName(field) {
  const labels = {
    name: "Name",
    dob: "Date of Birth",
    id_number: "ID Number",
    gender: "Gender",
  };

  return (
    labels[field] ||
    String(field || "Field")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase())
  );
}

function getFieldStatus(item) {
  if (
    item.submitted === null ||
    item.submitted === undefined ||
    String(item.submitted).trim() === ""
  ) {
    return "not-extracted";
  }

  if (
    item.status === "match" ||
    item.status === "matched" ||
    item.match === true ||
    item.is_match === true
  ) {
    return "match";
  }

  return "mismatch";
}

function App() {
  const [submittedFile, setSubmittedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  /*
   * Visual analysis animation.
   *
   * The actual completion of the analysis is controlled by the backend
   * response in handleAnalyze(). This animation only represents the
   * processing stages in the UI.
   */
  useEffect(() => {
    if (!isAnalyzing) {
      return undefined;
    }

    let stepIndex = 0;

    setCurrentStep(0);

    const interval = setInterval(() => {
      stepIndex += 1;

      if (stepIndex < analysisSteps.length) {
        setCurrentStep(stepIndex);
      }
    }, 1100);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSubmittedFile(file);
    setAnalysisComplete(false);
    setShowResults(false);
    setCurrentStep(-1);
    setAnalysisResult(null);
    setAnalysisError("");
  };

  const handleAnalyze = async () => {
    if (!submittedFile || isAnalyzing) {
      return;
    }

    setAnalysisComplete(false);
    setShowResults(false);
    setAnalysisError("");
    setAnalysisResult(null);
    setCurrentStep(0);
    setIsAnalyzing(true);

    try {
      /*
       * Step 1: Upload submitted document
       */
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
        let errorMessage = "Document upload failed.";

        try {
          const errorData = await uploadResponse.json();

          if (errorData?.detail) {
            errorMessage =
              typeof errorData.detail === "string"
                ? errorData.detail
                : "Document upload failed.";
          }
        } catch {
          // Keep the default error message.
        }

        throw new Error(errorMessage);
      }

      const uploadData = await uploadResponse.json();

      if (!uploadData?.document_id) {
        throw new Error(
          "Upload succeeded, but the backend did not return a document ID."
        );
      }

      /*
       * Step 2: Screen uploaded document
       */
      const screenResponse = await fetch(
        `${API_BASE_URL}/api/screen/${uploadData.document_id}`,
        {
          method: "POST",
        }
      );

      if (!screenResponse.ok) {
        let errorMessage = "Document screening failed.";

        try {
          const errorData = await screenResponse.json();

          if (errorData?.detail) {
            errorMessage =
              typeof errorData.detail === "string"
                ? errorData.detail
                : "Document screening failed.";
          }
        } catch {
          // Keep the default error message.
        }

        throw new Error(errorMessage);
      }

      const screenData = await screenResponse.json();

      /*
       * Store the real backend result.
       */
      setAnalysisResult(screenData);

      /*
       * Complete the visual pipeline only after the backend
       * has successfully returned the screening result.
       */
      setCurrentStep(analysisSteps.length - 1);
      setIsAnalyzing(false);
      setAnalysisComplete(true);
    } catch (error) {
      console.error("Analysis error:", error);

      setAnalysisError(
        error?.message ||
          "Something went wrong during document analysis."
      );

      setIsAnalyzing(false);
      setAnalysisComplete(false);
      setCurrentStep(-1);
    }
  };

  const handleReset = () => {
    setSubmittedFile(null);
    setIsAnalyzing(false);
    setAnalysisComplete(false);
    setShowResults(false);
    setCurrentStep(-1);
    setAnalysisResult(null);
    setAnalysisError("");
  };

  const riskClass = analysisResult
    ? getRiskClass(analysisResult.decision)
    : "";

  /*
   * Detect invalid-document result.
   */
  const isInvalidDocument =
    analysisResult?.decision === "INVALID DOCUMENT";

  /*
   * Prepare backend evidence data for the existing UI.
   *
   * Invalid documents should not be presented as if they
   * generated meaningful fraud-risk evidence.
   */
  const evidenceBreakdown =
    analysisResult?.evidence_breakdown || {};

  const evidenceItems = isInvalidDocument
    ? [
        {
          label: "Document Validity",
          score: 0,
          maxScore: 40,
        },
        {
          label: "OCR Screening",
          score: 0,
          maxScore: 40,
        },
        {
          label: "Tamper Analysis",
          score: 0,
          maxScore: 20,
        },
      ]
    : [
        {
          label: "Reference Comparison",
          score: Number(
            evidenceBreakdown.visual_risk_points ?? 0
          ),
          maxScore: 40,
        },
        {
          label: "OCR Consistency",
          score: Number(
            evidenceBreakdown.field_mismatch_points ?? 0
          ),
          maxScore: 40,
        },
        {
          label: "Tamper Indicators",
          score: Number(
            evidenceBreakdown.tamper_points ?? 0
          ),
          maxScore: 20,
        },
      ];

  /*
   * Build indicators from actual backend evidence.
   */
  const indicators = [];

  if (isInvalidDocument) {
    indicators.push(
      "The uploaded image did not contain enough recognizable document information for reliable screening."
    );

    indicators.push(
      "Fraud-risk analysis was not performed because the input was not recognized as a valid document."
    );

    indicators.push(
      "Please upload a clear PNG, JPG or JPEG document image containing readable document fields."
    );
  } else {
    if (analysisResult?.field_comparison) {
      const mismatchCount =
        analysisResult.field_comparison.mismatches?.length || 0;

      if (mismatchCount > 0) {
        indicators.push(
          `${mismatchCount} OCR field mismatch${
            mismatchCount === 1 ? "" : "es"
          } detected against the authorized reference.`
        );
      } else {
        indicators.push(
          "OCR-extracted document fields are consistent with the authorized reference."
        );
      }
    }

    const suspiciousRegionCount = Number(
      analysisResult?.tamper_evidence
        ?.suspicious_region_count ?? 0
    );

    if (suspiciousRegionCount > 0) {
      indicators.push(
        `${suspiciousRegionCount} suspicious visual region${
          suspiciousRegionCount === 1 ? "" : "s"
        } detected during tamper analysis.`
      );
    } else {
      indicators.push(
        "No suspicious visual regions were detected by the current tamper-analysis pipeline."
      );
    }

    const differencePercentage = Number(
      analysisResult?.difference_percentage ?? 0
    );

    const similarityScore = Number(
      analysisResult?.similarity_score ?? 0
    );

    if (differencePercentage > 0) {
      indicators.push(
        `Visual comparison detected ${differencePercentage.toFixed(
          2
        )}% image difference, with ${similarityScore.toFixed(
          2
        )}% similarity to the authorized reference.`
      );
    } else {
      indicators.push(
        `Visual comparison shows ${similarityScore.toFixed(
          2
        )}% similarity to the authorized reference.`
      );
    }

    if (analysisResult?.message) {
      indicators.push(analysisResult.message);
    }
  }

  /*
   * OCR field comparison from backend.
   *
   * The backend returns:
   * field_comparison.comparisons
   */
  const extractedFields = Object.entries(
    analysisResult?.field_comparison?.comparisons || {}
  ).map(([field, comparison]) => ({
    field,
    ...comparison,
  }));

  /*
   * Tamper-highlighted image returned by backend.
   */
  const highlightedImageUrl =
    analysisResult?.tamper_evidence
      ?.highlighted_image_url
      ? `${API_BASE_URL}${analysisResult.tamper_evidence.highlighted_image_url}`
      : null;

  /*
   * Results page
   */
  if (showResults && analysisResult) {
    return (
      <div className="app-shell">
        <nav className="navbar">
          <div className="brand">
            <div className="logo">
              <span>◈</span>
            </div>

            <div>
              <h2>DocShield</h2>
              <p>AI-Assisted Document Screening</p>
            </div>
          </div>

          <div className="nav-status">
            <span className="status-dot"></span>
            Analysis Complete
          </div>
        </nav>

        <main className="results-page">
          <section className="results-topbar">
            <button
              className="back-btn"
              type="button"
              onClick={() => setShowResults(false)}
            >
              ← Back to Analysis
            </button>

            <span>
              SCREENING RESULT • PAN-REF-001
            </span>
          </section>

          <section className={`result-hero ${riskClass}`}>
            <div>
              <span className="section-label">
                SCREENING DECISION
              </span>

              <h1>
                {analysisResult.decision === "CLEAR" && (
                  <>
                    Document appears
                    <span> consistent.</span>
                  </>
                )}

                {analysisResult.decision === "MANUAL REVIEW" && (
                  <>
                    Review
                    <span> recommended.</span>
                  </>
                )}

                {analysisResult.decision === "HIGH RISK" && (
                  <>
                    Further Verification
                    <span> Required.</span>
                  </>
                )}

                {analysisResult.decision ===
                  "INVALID DOCUMENT" && (
                  <>
                    Invalid
                    <span> Document.</span>
                  </>
                )}

                {![
                  "CLEAR",
                  "MANUAL REVIEW",
                  "HIGH RISK",
                  "INVALID DOCUMENT",
                ].includes(analysisResult.decision) && (
                  <>
                    Screening
                    <span> Result Available.</span>
                  </>
                )}
              </h1>

              <p>
                {analysisResult.message ||
                  "The screening pipeline has completed its analysis."}
              </p>
            </div>

            <div className="risk-score-card">
              <span>RISK SCORE</span>

              <div className="risk-number">
                <strong>
                  {Number(
                    analysisResult.risk_score ?? 0
                  ).toFixed(1)}
                </strong>

                <small>/ 100</small>
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
              {analysisResult.decision === "CLEAR"
                ? "✓"
                : analysisResult.decision ===
                  "INVALID DOCUMENT"
                  ? "⚠"
                  : "!"}
            </div>

            <div>
              <strong>Recommendation</strong>

              <p>
                {analysisResult.decision === "CLEAR"
                  ? "The submitted document appears consistent with the authorized reference. Proceed subject to normal human verification procedures."
                  : analysisResult.decision ===
                    "MANUAL REVIEW"
                    ? "Additional human verification is recommended before accepting the submitted document."
                    : analysisResult.decision ===
                      "INVALID DOCUMENT"
                    ? "The uploaded image could not be recognized as a valid document. Please upload a clear document image containing readable document information."
                    : "Further verification is required. The detected screening indicators should be reviewed by an authorized human verifier."}
              </p>
            </div>
          </section>

          <section className="results-grid">
            <div className="result-panel evidence-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    EVIDENCE BREAKDOWN
                  </span>

                  <h2>
                    {isInvalidDocument
                      ? "Why was this input rejected?"
                      : "Why was this result generated?"}
                  </h2>
                </div>

                <span className="panel-total">
                  {Number(
                    analysisResult.risk_score ?? 0
                  ).toFixed(1)}{" "}
                  / 100
                </span>
              </div>

              <div className="evidence-list">
                {evidenceItems.map((item) => {
                  const percentage =
                    item.maxScore > 0
                      ? Math.min(
                          100,
                          Math.max(
                            0,
                            (item.score / item.maxScore) *
                              100
                          )
                        )
                      : 0;

                  const status = getEvidenceStatus(
                    item.score,
                    item.maxScore
                  );

                  return (
                    <div
                      className="evidence-row"
                      key={item.label}
                    >
                      <div className="evidence-row-top">
                        <span>{item.label}</span>

                        <strong>
                          {item.score.toFixed(1)}/
                          {item.maxScore}
                        </strong>
                      </div>

                      <div className="evidence-bar">
                        <div
                          className={`evidence-fill ${status}`}
                          style={{
                            width: `${percentage}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {isInvalidDocument && (
                <p
                  style={{
                    marginTop: "20px",
                    color: "#64748b",
                    fontSize: "14px",
                    lineHeight: "1.6",
                  }}
                >
                  Fraud-risk scoring was skipped because the
                  uploaded image did not contain enough
                  recognizable document information.
                </p>
              )}
            </div>

            <div className="result-panel indicators-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    {isInvalidDocument
                      ? "INPUT VALIDATION"
                      : "DETECTED INDICATORS"}
                  </span>

                  <h2>
                    {isInvalidDocument
                      ? "Why can't this image be screened?"
                      : "Evidence summary"}
                  </h2>
                </div>
              </div>

              <div className="indicator-list">
                {indicators.map((indicator, index) => (
                  <div
                    className={`indicator-item ${riskClass}`}
                    key={`${indicator}-${index}`}
                  >
                    <span>{index + 1}</span>
                    <p>{indicator}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="result-panel field-comparison-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">
                  OCR FIELD COMPARISON
                </span>

                <h2>
                  Reference vs Submitted Document
                </h2>
              </div>

              <span className="comparison-badge">
                PAN-REF-001
              </span>
            </div>

            {isInvalidDocument ? (
              <div
                style={{
                  padding: "28px",
                  textAlign: "center",
                  color: "#64748b",
                }}
              >
                <strong
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    color: "#334155",
                  }}
                >
                  Document fields unavailable
                </strong>

                <span>
                  The uploaded image did not contain enough
                  recognizable document information for field
                  comparison.
                </span>
              </div>
            ) : (
              <div className="comparison-table">
                <div className="comparison-table-header">
                  <span>FIELD</span>
                  <span>AUTHORIZED REFERENCE</span>
                  <span>SUBMITTED DOCUMENT</span>
                  <span>STATUS</span>
                </div>

                {extractedFields.length > 0 ? (
                  extractedFields.map((item, index) => {
                    const fieldName =
                      item.field ||
                      item.name ||
                      `field_${index}`;

                    const status = getFieldStatus(item);

                    return (
                      <div
                        className="comparison-table-row"
                        key={`${fieldName}-${index}`}
                      >
                        <strong>
                          {formatFieldName(fieldName)}
                        </strong>

                        <span>
                          {item.reference ??
                            item.reference_value ??
                            "—"}
                        </span>

                        <span>
                          {item.submitted ??
                            item.submitted_value ??
                            "—"}
                        </span>

                        <span
                          className={`field-status ${
                            status === "match"
                              ? "match"
                              : status ===
                                "not-extracted"
                              ? "not-extracted"
                              : "mismatch"
                          }`}
                        >
                          {status === "match"
                            ? "✓ Match"
                            : status ===
                              "not-extracted"
                            ? "— Not Extracted"
                            : "⚠ Mismatch"}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="comparison-table-row">
                    <strong>OCR Fields</strong>

                    <span>—</span>

                    <span>
                      No structured fields were extracted.
                    </span>

                    <span className="field-status mismatch">
                      ⚠ Review
                    </span>
                  </div>
                )}
              </div>
            )}
          </section>

          {highlightedImageUrl && !isInvalidDocument && (
            <section className="result-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    VISUAL ANALYSIS
                  </span>

                  <h2>
                    Suspicious Region Highlight
                  </h2>
                </div>

                <span className="comparison-badge">
                  {analysisResult?.tamper_evidence
                    ?.suspicious_region_count ?? 0}{" "}
                  region
                  {Number(
                    analysisResult?.tamper_evidence
                      ?.suspicious_region_count ?? 0
                  ) === 1
                    ? ""
                    : "s"}
                </span>
              </div>

              <div
                style={{
                  marginTop: "20px",
                  textAlign: "center",
                }}
              >
                <img
                  src={highlightedImageUrl}
                  alt="Tamper analysis highlighting suspicious regions"
                  style={{
                    maxWidth: "100%",
                    maxHeight: "600px",
                    objectFit: "contain",
                    borderRadius: "12px",
                  }}
                />
              </div>
            </section>
          )}

          {isInvalidDocument && (
            <section className="result-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">
                    NEXT STEP
                  </span>

                  <h2>
                    Upload a valid document
                  </h2>
                </div>
              </div>

              <div
                style={{
                  padding: "10px 0 4px",
                  color: "#64748b",
                  lineHeight: "1.7",
                }}
              >
                <p>
                  DocShield could not reliably identify the
                  uploaded image as a document. For accurate
                  screening, upload a clear image of the
                  document containing readable text and
                  document fields.
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

                <h2>
                  Document analysis overview
                </h2>
              </div>
            </div>

            <div className="summary-grid">
              <div>
                <span>Reference</span>

                <strong>PAN-REF-001</strong>

                <small>
                  Authorized local prototype repository
                </small>
              </div>

              <div>
                <span>Submitted File</span>

                <strong>
                  {submittedFile?.name ||
                    "submitted_document"}
                </strong>

                <small>
                  Document screened in current session
                </small>
              </div>

              <div>
                <span>Decision</span>

                <strong
                  className={`${riskClass}-risk-text`}
                >
                  {analysisResult.decision}
                </strong>

                <small>
                  {isInvalidDocument
                    ? "Input validation result"
                    : "Evidence-based screening recommendation"}
                </small>
              </div>

              <div>
                <span>Final Action</span>

                <strong>
                  {analysisResult.decision === "CLEAR"
                    ? "Proceed"
                    : analysisResult.decision ===
                      "INVALID DOCUMENT"
                    ? "Upload Valid Document"
                    : "Manual Review"}
                </strong>

                <small>
                  {isInvalidDocument
                    ? "Provide a recognizable document image"
                    : "Authorized human verification remains available"}
                </small>
              </div>
            </div>
          </section>

          <section className="results-disclaimer">
            <div className="shield">🛡</div>

            <div>
              <h3>
                Explainable Decision-Support
              </h3>

              <p>
                DocShield provides an evidence-based
                screening recommendation. A high-risk or
                manual-review result indicates document
                indicators requiring further verification.
                An invalid-document result means the input
                could not be reliably screened. The system
                does not establish fraud or legally
                authenticate a document. Final decisions
                remain with the authorized human verifier.
              </p>
            </div>
          </section>

          <div className="results-actions">
            <button
              className="secondary-action-btn"
              type="button"
              onClick={handleReset}
            >
              Screen Another Document
            </button>

            <button
              className="primary-action-btn"
              type="button"
              onClick={handleReset}
            >
              Start New Screening →
            </button>
          </div>
        </main>

        <footer>
          <p>
            DocShield-SIH2026 • Explainable Document
            Screening Prototype
          </p>
        </footer>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <div className="logo">
            <span>◈</span>
          </div>

          <div>
            <h2>DocShield</h2>
            <p>AI-Assisted Document Screening</p>
          </div>
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          Local Prototype
        </div>
      </nav>

      <main>
        <section className="hero">
          <div className="hero-badge">
            SIH 2026 • MHA
          </div>

          <h1>
            Screen Documents.
            <span> Understand Risk.</span>
          </h1>

          <p>
            Upload a submitted document and compare it
            against an authorized reference already stored
            in DocShield. Our evidence-based pipeline
            combines OCR consistency, visual comparison,
            tamper indicators and document rules.
          </p>
        </section>

        <section className="workflow">
          <div className="step active">
            <span>1</span>
            Reference Loaded
          </div>

          <div className="line"></div>

          <div
            className={`step ${
              submittedFile ? "active" : ""
            }`}
          >
            <span>2</span>
            Upload Document
          </div>

          <div className="line"></div>

          <div
            className={`step ${
              isAnalyzing ? "active" : ""
            }`}
          >
            <span>3</span>
            Analyze Evidence
          </div>

          <div className="line"></div>

          <div
            className={`step ${
              analysisComplete ? "active" : ""
            }`}
          >
            <span>4</span>
            Review Risk
          </div>
        </section>

        <section className="comparison-layout">
          <div className="reference-card">
            <div className="reference-header">
              <div className="icon-box blue">✓</div>

              <div>
                <span className="card-label">
                  AUTHORIZED REFERENCE
                </span>

                <h3>Reference Document</h3>
              </div>
            </div>

            <div className="reference-status">
              <span className="status-check">✓</span>

              <div>
                <strong>Reference Available</strong>

                <p>
                  Loaded automatically from secure
                  repository
                </p>
              </div>
            </div>

            <div className="reference-details">
              <div>
                <span>Document Type</span>
                <strong>PAN Card</strong>
              </div>

              <div>
                <span>Reference ID</span>
                <strong>PAN-REF-001</strong>
              </div>

              <div>
                <span>Holder</span>
                <strong>ARJUN SHARMA</strong>
              </div>

              <div>
                <span>Status</span>
                <strong className="verified">
                  Verified Reference
                </strong>
              </div>
            </div>

            <div className="repository-note">
              <span>◉</span>
              Authorized reference stored locally for
              prototype
            </div>
          </div>

          <div className="upload-card">
            <div className="card-top">
              <div className="icon-box orange">🔍</div>

              <div>
                <span className="card-label">
                  DOCUMENT TO SCREEN
                </span>

                <h3>Submitted Document</h3>
              </div>
            </div>

            <label className="upload-zone">
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.pdf"
                onChange={handleFileChange}
                disabled={isAnalyzing}
              />

              <div className="upload-content">
                <div className="upload-icon">
                  {submittedFile ? "✓" : "⇧"}
                </div>

                <h4>
                  {submittedFile
                    ? submittedFile.name
                    : "Upload submitted document"}
                </h4>

                <p>
                  {submittedFile
                    ? "Click to replace the selected document"
                    : "PNG, JPG or PDF"}
                </p>
              </div>
            </label>

            {submittedFile && (
              <div className="file-success">
                <span>✓</span>
                Document ready for screening
              </div>
            )}

            {analysisError && (
              <div
                className="file-success"
                style={{
                  marginTop: "12px",
                }}
              >
                <span>⚠</span>
                {analysisError}
              </div>
            )}
          </div>
        </section>

        <section className="pipeline">
          <div className="pipeline-heading">
            <span className="section-label">
              ANALYSIS PIPELINE
            </span>

            <h2>
              Reference <span>vs</span> Submitted Document
            </h2>

            <p>
              DocShield evaluates multiple independent
              evidence signals before generating a
              screening recommendation.
            </p>
          </div>

          <div className="pipeline-flow">
            <div className="pipeline-item">
              <div>🔤</div>
              <strong>OCR</strong>
              <span>Text extraction</span>
            </div>

            <div className="pipeline-arrow">→</div>

            <div className="pipeline-item">
              <div>◫</div>
              <strong>Visual Diff</strong>
              <span>Image comparison</span>
            </div>

            <div className="pipeline-arrow">→</div>

            <div className="pipeline-item">
              <div>⚠</div>
              <strong>Tamper</strong>
              <span>Anomaly detection</span>
            </div>

            <div className="pipeline-arrow">→</div>

            <div className="pipeline-item">
              <div>✓</div>
              <strong>Rules</strong>
              <span>Format validation</span>
            </div>

            <div className="pipeline-arrow">→</div>

            <div className="pipeline-item final">
              <div>◈</div>
              <strong>Risk Engine</strong>
              <span>Evidence fusion</span>
            </div>
          </div>
        </section>

        {isAnalyzing && (
          <section className="analysis-panel">
            <div className="analysis-header">
              <div>
                <span className="section-label">
                  LIVE ANALYSIS
                </span>

                <h2>
                  Analyzing Submitted Document
                </h2>

                <p>
                  DocShield is evaluating the document
                  against the authorized reference.
                </p>
              </div>

              <div className="analysis-spinner"></div>
            </div>

            <div className="analysis-steps">
              {analysisSteps.map((step, index) => {
                const isComplete =
                  index < currentStep;
                const isCurrent =
                  index === currentStep;

                return (
                  <div
                    className={`analysis-step ${
                      isComplete ? "complete" : ""
                    } ${
                      isCurrent ? "current" : ""
                    }`}
                    key={step.title}
                  >
                    <div className="analysis-step-icon">
                      {isComplete ? "✓" : step.icon}
                    </div>

                    <div className="analysis-step-content">
                      <strong>{step.title}</strong>

                      <span>
                        {isCurrent
                          ? "Processing..."
                          : isComplete
                          ? "Completed"
                          : step.description}
                      </span>
                    </div>

                    <div className="analysis-step-status">
                      {isComplete && "✓"}

                      {isCurrent && (
                        <span className="mini-spinner"></span>
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
                  width: `${Math.max(
                    5,
                    ((currentStep + 1) /
                      analysisSteps.length) *
                      100
                  )}%`,
                }}
              ></div>
            </div>

            <p className="analysis-note">
              Processing locally for prototype
              demonstration.
            </p>
          </section>
        )}

        {analysisComplete && analysisResult && (
          <section className="analysis-complete">
            <div className="complete-icon">✓</div>

            <div>
              <span className="section-label">
                ANALYSIS COMPLETE
              </span>

              <h2>
                Evidence analysis finished successfully
              </h2>

              <p>
                The document has passed through OCR,
                reference comparison, tamper analysis,
                document rules and the risk assessment
                stage.
              </p>
            </div>

            <button
              className="view-results-btn"
              type="button"
              onClick={() => setShowResults(true)}
            >
              View Screening Result
              <span>→</span>
            </button>
          </section>
        )}

        {!isAnalyzing && !analysisComplete && (
          <section className="analyze-section">
            <button
              className={`analyze-btn ${
                submittedFile ? "enabled" : ""
              }`}
              disabled={!submittedFile}
              onClick={handleAnalyze}
              type="button"
            >
              Analyze Submitted Document
              <span>→</span>
            </button>

            <p>
              The authorized reference will be
              automatically used for comparison.
            </p>
          </section>
        )}

        {analysisComplete && (
          <div className="reset-container">
            <button
              className="reset-btn"
              onClick={handleReset}
              type="button"
            >
              Analyze Another Document
            </button>
          </div>
        )}

        <section className="disclaimer">
          <div className="shield">🛡</div>

          <div>
            <h3>Decision-Support System</h3>

            <p>
              DocShield is an AI-assisted screening tool.
              A high-risk result indicates document
              indicators requiring further verification. An
              invalid-document result means the input could
              not be reliably screened. It does not
              establish fraud or provide legally binding
              authentication. Final verification remains with
              the authorized human officer.
            </p>
          </div>
        </section>
      </main>

      <footer>
        <p>
          DocShield-SIH2026 • Smart India Hackathon
          Prototype
        </p>
      </footer>
    </div>
  );
}

export default App;