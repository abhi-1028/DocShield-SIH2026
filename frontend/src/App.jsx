import { useEffect, useState } from "react";
import "./App.css";

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

function getRiskClass(decision = "") {
  const normalized = decision.toUpperCase();

  if (normalized === "CLEAR") {
    return "clear";
  }

  if (
    normalized.includes("REVIEW") ||
    normalized.includes("MANUAL")
  ) {
    return "review";
  }

  return "high";
}

function normalizeResult(data) {
  const evidenceBreakdown = data.evidence_breakdown || {};

  const evidence = [
    {
      label: "Visual Comparison",
      score: Number(evidenceBreakdown.visual_risk_points ?? 0),
      maxScore: 40,
    },
    {
      label: "Field Comparison",
      score: Number(evidenceBreakdown.field_mismatch_points ?? 0),
      maxScore: 30,
    },
    {
      label: "Tamper Detection",
      score: Number(evidenceBreakdown.tamper_points ?? 0),
      maxScore: 20,
    },
    {
      label: "Visual Difference",
      score: Number(
        evidenceBreakdown.visual_difference_percentage ?? 0
      ),
      maxScore: 10,
    },
  ];

  const comparisons =
    data.field_comparison?.comparisons || {};

  const extractedFields = Object.entries(comparisons).map(
    ([field, value]) => ({
      field: field.toUpperCase(),
      reference: value.reference || "-",
      submitted: value.submitted || "-",
      status: value.match ? "match" : "mismatch",
    })
  );

  const decision = data.decision || "MANUAL REVIEW";

  const suspiciousCount =
    data.tamper_evidence?.suspicious_region_count || 0;

  const indicators = [];

  indicators.push(
    `Similarity score: ${data.similarity_score ?? 0}%`
  );

  indicators.push(
    `Visual difference: ${
      data.difference_percentage ?? 0
    }%`
  );

  indicators.push(
    `Field match percentage: ${
      data.field_comparison?.match_percentage ?? 0
    }%`
  );

  indicators.push(
    `Suspicious regions detected: ${suspiciousCount}`
  );

  if (data.message) {
    indicators.push(data.message);
  }

  return {
    riskScore: Number(data.risk_score ?? 0),

    decision,

    recommendation:
      data.message ||
      "Document screening completed successfully.",

    description:
      data.message ||
      "The document has been evaluated using OCR, visual comparison, tamper detection and document rules.",

    evidence: evidence.map((item) => {
      let status = "low";

      if (item.score > item.maxScore * 0.7) {
        status = "high";
      } else if (item.score > item.maxScore * 0.35) {
        status = "medium";
      }

      return {
        ...item,
        status,
      };
    }),
    indicators,
    extractedFields,
    raw: data,
  };
}

function App() {
  const [submittedFile, setSubmittedFile] =
    useState(null);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [currentStep, setCurrentStep] =
    useState(-1);

  const [analysisComplete, setAnalysisComplete] =
    useState(false);

  const [showResults, setShowResults] =
    useState(false);

  const [analysisResult, setAnalysisResult] =
    useState(null);

  const [errorMessage, setErrorMessage] =
    useState("");

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
      } else {
        clearInterval(interval);
      }
    }, 900);

    return () => {
      clearInterval(interval);
    };
  }, [isAnalyzing]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSubmittedFile(file);

    setAnalysisResult(null);

    setErrorMessage("");

    setAnalysisComplete(false);

    setShowResults(false);

    setCurrentStep(-1);
  };

  const handleAnalyze = async () => {
    if (!submittedFile || isAnalyzing) {
      return;
    }

    setErrorMessage("");

    setAnalysisResult(null);

    setAnalysisComplete(false);

    setShowResults(false);

    setCurrentStep(0);

    setIsAnalyzing(true);

    try {
      /*
        STEP 1
        Upload the selected document.
      */

      const formData = new FormData();

      formData.append("file", submittedFile);

      const uploadResponse = await fetch(
        "http://127.0.0.1:8000/api/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!uploadResponse.ok) {
        const errorData =
          await uploadResponse.json();

        throw new Error(
          errorData.detail ||
            "Unable to upload the document."
        );
      }

      const uploadData =
        await uploadResponse.json();

      const documentId =
        uploadData.document_id;

      if (!documentId) {
        throw new Error(
          "Backend did not return a document ID."
        );
      }

      /*
        STEP 2
        Send the uploaded document ID
        to the screening endpoint.
      */

      const screenResponse = await fetch(
        `http://127.0.0.1:8000/api/screen/${documentId}`,
        {
          method: "POST",
        }
      );

      if (!screenResponse.ok) {
        const errorData =
          await screenResponse.json();

        throw new Error(
          errorData.detail ||
            "Unable to analyze the document."
        );
      }

      const result =
        await screenResponse.json();

      console.log(
        "SCREENING RESULT:",
        result
      );

      /*
        Convert backend result into
        frontend display format.
      */

      const normalizedResult =
        normalizeResult(result);

      setAnalysisResult(
        normalizedResult
      );

      setCurrentStep(
        analysisSteps.length - 1
      );

      setTimeout(() => {
        setIsAnalyzing(false);

        setAnalysisComplete(true);
      }, 700);
    } catch (error) {
      console.error(
        "Analysis error:",
        error
      );

      setIsAnalyzing(false);

      setAnalysisComplete(false);

      setCurrentStep(-1);

      setErrorMessage(
        `Unable to analyze the document. ${
          error.message ||
          "Unknown error"
        }`
      );
    }
  };

  const handleReset = () => {
    setSubmittedFile(null);

    setIsAnalyzing(false);

    setAnalysisComplete(false);

    setShowResults(false);

    setCurrentStep(-1);

    setAnalysisResult(null);

    setErrorMessage("");
  };

  const selectedResult =
    analysisResult;

  const riskClass =
    getRiskClass(
      selectedResult?.decision ||
        "MANUAL REVIEW"
    );

  if (
    showResults &&
    selectedResult
  ) {
    return (
      <div className="app-shell">

        <nav className="navbar">

          <div className="brand">

            <div className="logo">
              <span>◈</span>
            </div>

            <div>
              <h2>DocShield</h2>

              <p>
                AI-Assisted Document Screening
              </p>
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
              onClick={() =>
                setShowResults(false)
              }
            >
              ← Back to Analysis
            </button>

            <span>
              SCREENING RESULT
            </span>

          </section>

          <section
            className={`result-hero ${riskClass}`}
          >

            <div>

              <span className="section-label">
                SCREENING DECISION
              </span>

              <h1>

                {selectedResult.decision ===
                  "CLEAR" && (
                  <>
                    Document appears
                    <span>
                      {" "}
                      consistent.
                    </span>
                  </>
                )}

                {selectedResult.decision !==
                  "CLEAR" &&
                  riskClass === "review" && (
                    <>
                      Review
                      <span>
                        {" "}
                        recommended.
                      </span>
                    </>
                  )}

                {riskClass === "high" && (
                  <>
                    Further Verification
                    <span>
                      {" "}
                      Required.
                    </span>
                  </>
                )}

              </h1>

              <p>
                {selectedResult.description}
              </p>

            </div>

            <div className="risk-score-card">

              <span>
                RISK SCORE
              </span>

              <div className="risk-number">

                <strong>
                  {selectedResult.riskScore}
                </strong>

                <small>
                  / 100
                </small>

              </div>

              <div className="risk-label">
                {selectedResult.decision}
              </div>

            </div>

          </section>

          <section
            className={`recommendation-banner ${riskClass}`}
          >

            <div className="recommendation-icon">

              {selectedResult.decision ===
              "CLEAR"
                ? "✓"
                : "!"}

            </div>

            <div>

              <strong>
                Recommendation
              </strong>

              <p>
                {selectedResult.recommendation}
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
                    Why was this result generated?
                  </h2>

                </div>

                <span className="panel-total">

                  {selectedResult.riskScore}
                  {" "}
                  / 100

                </span>

              </div>

              <div className="evidence-list">

                {selectedResult.evidence.map(
                  (item, index) => {

                    const percentage =
                      item.maxScore > 0
                        ? Math.min(
                            100,
                            (item.score /
                              item.maxScore) *
                              100
                          )
                        : 0;

                    return (
                      <div
                        className="evidence-row"
                        key={`${item.label}-${index}`}
                      >

                        <div className="evidence-row-top">

                          <span>
                            {item.label}
                          </span>

                          <strong>

                            {item.score}
                            /
                            {item.maxScore}

                          </strong>

                        </div>

                        <div className="evidence-bar">

                          <div
                            className={`evidence-fill ${item.status}`}
                            style={{
                              width:
                                `${percentage}%`,
                            }}
                          ></div>

                        </div>

                      </div>
                    );
                  }
                )}

              </div>

            </div>

            <div className="result-panel indicators-panel">

              <div className="panel-heading">

                <div>

                  <span className="section-label">
                    DETECTED INDICATORS
                  </span>

                  <h2>
                    Evidence summary
                  </h2>

                </div>

              </div>

              <div className="indicator-list">

                {selectedResult.indicators.map(
                  (indicator, index) => (

                    <div
                      className={`indicator-item ${riskClass}`}
                      key={`${indicator}-${index}`}
                    >

                      <span>
                        {index + 1}
                      </span>

                      <p>
                        {indicator}
                      </p>

                    </div>
                  )
                )}

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

            </div>

            <div className="comparison-table">

              <div className="comparison-table-header">

                <span>FIELD</span>

                <span>
                  AUTHORIZED REFERENCE
                </span>

                <span>
                  SUBMITTED DOCUMENT
                </span>

                <span>
                  STATUS
                </span>

              </div>

              {selectedResult.extractedFields
                .length > 0 ? (

                selectedResult.extractedFields.map(
                  (item, index) => (

                    <div
                      className="comparison-table-row"
                      key={`${item.field}-${index}`}
                    >

                      <strong>
                        {item.field}
                      </strong>

                      <span>
                        {item.reference}
                      </span>

                      <span>
                        {item.submitted}
                      </span>

                      <span
                        className={`field-status ${
                          item.status === "match"
                            ? "match"
                            : "mismatch"
                        }`}
                      >

                        {item.status === "match"
                          ? "✓ Match"
                          : "⚠ Mismatch"}

                      </span>

                    </div>
                  )
                )

              ) : (

                <div className="comparison-table-row">

                  <strong>
                    No fields available
                  </strong>

                  <span>-</span>

                  <span>-</span>

                  <span>-</span>

                </div>

              )}

            </div>

          </section>

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

                <span>
                  Submitted File
                </span>

                <strong>
                  {submittedFile?.name ||
                    "submitted_document"}
                </strong>

                <small>
                  Document screened in current session
                </small>

              </div>

              <div>

                <span>
                  Decision
                </span>

                <strong
                  className={`${riskClass}-risk-text`}
                >
                  {selectedResult.decision}
                </strong>

                <small>
                  Evidence-based screening recommendation
                </small>

              </div>

              <div>

                <span>
                  Similarity Score
                </span>

                <strong>
                  {selectedResult.raw
                    ?.similarity_score ?? 0}
                  %
                </strong>

                <small>
                  Reference comparison result
                </small>

              </div>

              <div>

                <span>
                  Final Action
                </span>

                <strong>

                  {selectedResult.decision ===
                  "CLEAR"
                    ? "Proceed"
                    : "Manual Review"}

                </strong>

                <small>
                  Human verification remains available
                </small>

              </div>

            </div>

          </section>

          <section className="results-disclaimer">

            <div className="shield">
              🛡
            </div>

            <div>

              <h3>
                Explainable Decision-Support
              </h3>

              <p>
                DocShield provides an
                evidence-based screening
                recommendation. Final decisions
                remain with the authorized human
                verifier.
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

          </div>

        </main>

        <footer>

          <p>
            DocShield-SIH2026 • Explainable
            Document Screening Prototype
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

            <h2>
              DocShield
            </h2>

            <p>
              AI-Assisted Document Screening
            </p>

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

            <span>
              {" "}
              Understand Risk.
            </span>

          </h1>

          <p>

            Upload a submitted document and
            compare it against an authorized
            reference stored in DocShield.

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
              submittedFile
                ? "active"
                : ""
            }`}
          >

            <span>2</span>

            Upload Document

          </div>

          <div className="line"></div>

          <div
            className={`step ${
              isAnalyzing
                ? "active"
                : ""
            }`}
          >

            <span>3</span>

            Analyze Evidence

          </div>

          <div className="line"></div>

          <div
            className={`step ${
              analysisComplete
                ? "active"
                : ""
            }`}
          >

            <span>4</span>

            Review Risk

          </div>

        </section>

        <section className="comparison-layout">

          <div className="reference-card">

            <div className="reference-header">

              <div className="icon-box blue">
                ✓
              </div>

              <div>

                <span className="card-label">
                  AUTHORIZED REFERENCE
                </span>

                <h3>
                  Reference Document
                </h3>

              </div>

            </div>

            <div className="reference-status">

              <span className="status-check">
                ✓
              </span>

              <div>

                <strong>
                  Reference Available
                </strong>

                <p>
                  Loaded automatically from
                  secure repository
                </p>

              </div>

            </div>

          </div>

          <div className="upload-card">

            <div className="card-top">

              <div className="icon-box orange">
                🔍
              </div>

              <div>

                <span className="card-label">
                  DOCUMENT TO SCREEN
                </span>

                <h3>
                  Submitted Document
                </h3>

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

                  {submittedFile
                    ? "✓"
                    : "⇧"}

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

          </div>

        </section>

        <section className="pipeline">

          <div className="pipeline-heading">

            <span className="section-label">
              ANALYSIS PIPELINE
            </span>

            <h2>

              Reference
              {" "}
              <span>vs</span>
              {" "}
              Submitted Document

            </h2>

            <p>

              DocShield evaluates multiple
              independent evidence signals.

            </p>

          </div>

          <div className="pipeline-flow">

            <div className="pipeline-item">
              <div>🔤</div>
              <strong>OCR</strong>
              <span>Text extraction</span>
            </div>

            <div className="pipeline-arrow">
              →
            </div>

            <div className="pipeline-item">
              <div>◫</div>
              <strong>Visual Diff</strong>
              <span>Image comparison</span>
            </div>

            <div className="pipeline-arrow">
              →
            </div>

            <div className="pipeline-item">
              <div>💀</div>
              <strong>Tamper</strong>
              <span>Anomaly detection</span>
            </div>

            <div className="pipeline-arrow">
              →
            </div>

            <div className="pipeline-item">
              <div>✓</div>
              <strong>Rules</strong>
              <span>Format validation</span>
            </div>

            <div className="pipeline-arrow">
              →
            </div>

            <div className="pipeline-item final">
              <div>◈</div>
              <strong>Risk Engine</strong>
              <span>Evidence fusion</span>
            </div>

          </div>

        </section>

        {errorMessage && (

          <section
            style={{
              margin: "20px auto",
              maxWidth: "900px",
              padding: "16px",
              borderRadius: "12px",
            }}
          >

            <strong>
              Backend Error:
            </strong>

            <p>
              {errorMessage}
            </p>

          </section>

        )}

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
                  DocShield is evaluating the
                  document against the
                  authorized reference.
                </p>

              </div>

              <div className="analysis-spinner"></div>

            </div>

            <div className="analysis-steps">

              {analysisSteps.map(
                (step, index) => {

                  const isComplete =
                    index < currentStep;

                  const isCurrent =
                    index === currentStep;

                  return (
                    <div
                      className={`analysis-step ${
                        isComplete
                          ? "complete"
                          : ""
                      } ${
                        isCurrent
                          ? "current"
                          : ""
                      }`}
                      key={step.title}
                    >

                      <div className="analysis-step-icon">

                        {isComplete
                          ? "✓"
                          : step.icon}

                      </div>

                      <div className="analysis-step-content">

                        <strong>
                          {step.title}
                        </strong>

                        <span>

                          {isCurrent
                            ? "Processing..."
                            : isComplete
                              ? "Completed"
                              : step.description}

                        </span>

                      </div>

                    </div>
                  );
                }
              )}

            </div>

          </section>

        )}

        {analysisComplete &&
          analysisResult && (

            <section className="analysis-complete">

              <div className="complete-icon">
                ✓
              </div>

              <div>

                <span className="section-label">
                  ANALYSIS COMPLETE
                </span>

                <h2>
                  Evidence analysis finished successfully
                </h2>

                <p>
                  The document has passed through
                  the DocShield screening pipeline.
                </p>

              </div>

              <button
                className="view-results-btn"
                type="button"
                onClick={() =>
                  setShowResults(true)
                }
              >

                View Screening Result

                <span>→</span>

              </button>

            </section>

          )}

        {!isAnalyzing &&
          !analysisComplete && (

            <section className="analyze-section">

              <button
                className={`analyze-btn ${
                  submittedFile
                    ? "enabled"
                    : ""
                }`}
                disabled={!submittedFile}
                onClick={handleAnalyze}
                type="button"
              >

                Analyze Submitted Document

                <span>→</span>

              </button>

              <p>
                The authorized reference will
                automatically be used for
                comparison.
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

          <div className="shield">
            🛡
          </div>

          <div>

            <h3>
              Decision-Support System
            </h3>

            <p>
              DocShield is an AI-assisted
              screening tool. Final verification
              remains with the authorized human
              officer.
            </p>

          </div>

        </section>

      </main>

      <footer>

        <p>
          DocShield-SIH2026 • Smart India
          Hackathon Prototype
        </p>

      </footer>

    </div>
  );
}

export default App;