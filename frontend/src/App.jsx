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

const demoResults = {
  clear: {
    riskScore: 8,
    decision: "CLEAR",
    recommendation: "No significant indicators detected",
    description:
      "The submitted document is consistent with the authorized reference across the evaluated evidence signals.",
    evidence: [
      {
        label: "Reference Comparison",
        score: 3,
        maxScore: 40,
        status: "low",
      },
      {
        label: "OCR Consistency",
        score: 2,
        maxScore: 30,
        status: "low",
      },
      {
        label: "Tamper Indicators",
        score: 1,
        maxScore: 20,
        status: "low",
      },
      {
        label: "Document Rules",
        score: 2,
        maxScore: 10,
        status: "low",
      },
    ],
    indicators: [
      "No significant visual difference detected",
      "Extracted fields are consistent with the reference",
      "Document format and field rules passed",
    ],
    extractedFields: [
      {
        field: "Name",
        reference: "ARJUN SHARMA",
        submitted: "ARJUN SHARMA",
        status: "match",
      },
      {
        field: "Date of Birth",
        reference: "14/08/2002",
        submitted: "14/08/2002",
        status: "match",
      },
      {
        field: "PAN Number",
        reference: "ABCDE1234F",
        submitted: "ABCDE1234F",
        status: "match",
      },
    ],
  },

  review: {
    riskScore: 47,
    decision: "MANUAL REVIEW",
    recommendation: "Review recommended before acceptance",
    description:
      "The document contains a limited inconsistency that should be checked by an authorized human verifier.",
    evidence: [
      {
        label: "Reference Comparison",
        score: 17,
        maxScore: 40,
        status: "medium",
      },
      {
        label: "OCR Consistency",
        score: 15,
        maxScore: 30,
        status: "medium",
      },
      {
        label: "Tamper Indicators",
        score: 10,
        maxScore: 20,
        status: "medium",
      },
      {
        label: "Document Rules",
        score: 5,
        maxScore: 10,
        status: "low",
      },
    ],
    indicators: [
      "Date of birth differs from the authorized reference",
      "Localized visual difference detected",
      "Additional verification recommended",
    ],
    extractedFields: [
      {
        field: "Name",
        reference: "ARJUN SHARMA",
        submitted: "ARJUN SHARMA",
        status: "match",
      },
      {
        field: "Date of Birth",
        reference: "14/08/2002",
        submitted: "14/08/2003",
        status: "mismatch",
      },
      {
        field: "PAN Number",
        reference: "ABCDE1234F",
        submitted: "ABCDE1234F",
        status: "match",
      },
    ],
  },

  high: {
    riskScore: 88,
    decision: "HIGH RISK",
    recommendation: "Manual verification required",
    description:
      "Multiple evidence signals require this document to be reviewed by an authorized human verifier.",
    evidence: [
      {
        label: "Reference Comparison",
        score: 35,
        maxScore: 40,
        status: "high",
      },
      {
        label: "OCR Consistency",
        score: 25,
        maxScore: 30,
        status: "medium",
      },
      {
        label: "Tamper Indicators",
        score: 20,
        maxScore: 20,
        status: "high",
      },
      {
        label: "Document Rules",
        score: 8,
        maxScore: 10,
        status: "low",
      },
    ],
    indicators: [
      "Date of birth differs from the authorized reference",
      "Localized visual difference detected in a document field",
      "Text region shows possible modification",
    ],
    extractedFields: [
      {
        field: "Name",
        reference: "ARJUN SHARMA",
        submitted: "ARJUN SHARMA",
        status: "match",
      },
      {
        field: "Date of Birth",
        reference: "14/08/2002",
        submitted: "14/08/2003",
        status: "mismatch",
      },
      {
        field: "PAN Number",
        reference: "ABCDE1234F",
        submitted: "ABCDE1234F",
        status: "match",
      },
    ],
  },
};

function getRiskClass(decision) {
  if (decision === "CLEAR") {
    return "clear";
  }

  if (decision === "MANUAL REVIEW") {
    return "review";
  }

  return "high";
}

function App() {
  const [submittedFile, setSubmittedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [demoMode, setDemoMode] = useState("high");

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

        setTimeout(() => {
          setIsAnalyzing(false);
          setAnalysisComplete(true);
        }, 700);
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
  };

  const handleAnalyze = () => {
    if (!submittedFile || isAnalyzing) {
      return;
    }

    setAnalysisComplete(false);
    setShowResults(false);
    setCurrentStep(0);
    setIsAnalyzing(true);
  };

  const handleReset = () => {
    setSubmittedFile(null);
    setIsAnalyzing(false);
    setAnalysisComplete(false);
    setShowResults(false);
    setCurrentStep(-1);
  };

  const selectedResult = demoResults[demoMode];
  const riskClass = getRiskClass(selectedResult.decision);

  if (showResults) {
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

            <span>SCREENING RESULT • PAN-REF-001</span>
          </section>

          <section className={`result-hero ${riskClass}`}>
            <div>
              <span className="section-label">SCREENING DECISION</span>

              <h1>
                {selectedResult.decision === "CLEAR" && (
                  <>
                    Document appears
                    <span> consistent.</span>
                  </>
                )}

                {selectedResult.decision === "MANUAL REVIEW" && (
                  <>
                    Review
                    <span> recommended.</span>
                  </>
                )}

                {selectedResult.decision === "HIGH RISK" && (
                  <>
                    Further Verification
                    <span> Required.</span>
                  </>
                )}
              </h1>

              <p>{selectedResult.description}</p>
            </div>

            <div className="risk-score-card">
              <span>RISK SCORE</span>

              <div className="risk-number">
                <strong>{selectedResult.riskScore}</strong>
                <small>/ 100</small>
              </div>

              <div className="risk-label">{selectedResult.decision}</div>
            </div>
          </section>

          <section className={`recommendation-banner ${riskClass}`}>
            <div className="recommendation-icon">
              {selectedResult.decision === "CLEAR"
                ? "✓"
                : selectedResult.decision === "MANUAL REVIEW"
                  ? "!"
                  : "!"}
            </div>

            <div>
              <strong>Recommendation</strong>
              <p>{selectedResult.recommendation}</p>
            </div>
          </section>

          <section className="results-grid">
            <div className="result-panel evidence-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">EVIDENCE BREAKDOWN</span>
                  <h2>Why was this result generated?</h2>
                </div>

                <span className="panel-total">
                  {selectedResult.riskScore} / 100
                </span>
              </div>

              <div className="evidence-list">
                {selectedResult.evidence.map((item) => {
                  const percentage = (item.score / item.maxScore) * 100;

                  return (
                    <div className="evidence-row" key={item.label}>
                      <div className="evidence-row-top">
                        <span>{item.label}</span>

                        <strong>
                          {item.score}/{item.maxScore}
                        </strong>
                      </div>

                      <div className="evidence-bar">
                        <div
                          className={`evidence-fill ${item.status}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="result-panel indicators-panel">
              <div className="panel-heading">
                <div>
                  <span className="section-label">DETECTED INDICATORS</span>
                  <h2>Evidence summary</h2>
                </div>
              </div>

              <div className="indicator-list">
                {selectedResult.indicators.map((indicator, index) => (
                  <div
                    className={`indicator-item ${riskClass}`}
                    key={indicator}
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
                <span className="section-label">OCR FIELD COMPARISON</span>
                <h2>Reference vs Submitted Document</h2>
              </div>

              <span className="comparison-badge">PAN-REF-001</span>
            </div>

            <div className="comparison-table">
              <div className="comparison-table-header">
                <span>FIELD</span>
                <span>AUTHORIZED REFERENCE</span>
                <span>SUBMITTED DOCUMENT</span>
                <span>STATUS</span>
              </div>

              {selectedResult.extractedFields.map((item) => (
                <div className="comparison-table-row" key={item.field}>
                  <strong>{item.field}</strong>

                  <span>{item.reference}</span>

                  <span>{item.submitted}</span>

                  <span
                    className={`field-status ${
                      item.status === "match" ? "match" : "mismatch"
                    }`}
                  >
                    {item.status === "match" ? "✓ Match" : "⚠ Mismatch"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="result-panel document-summary-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">SCREENING SUMMARY</span>
                <h2>Document analysis overview</h2>
              </div>
            </div>

            <div className="summary-grid">
              <div>
                <span>Reference</span>
                <strong>PAN-REF-001</strong>
                <small>Authorized local prototype repository</small>
              </div>

              <div>
                <span>Submitted File</span>
                <strong>{submittedFile?.name || "submitted_document"}</strong>
                <small>Document screened in current session</small>
              </div>

              <div>
                <span>Decision</span>
                <strong className={`${riskClass}-risk-text`}>
                  {selectedResult.decision}
                </strong>
                <small>Evidence-based screening recommendation</small>
              </div>

              <div>
                <span>Final Action</span>
                <strong>
                  {selectedResult.decision === "CLEAR"
                    ? "Proceed"
                    : "Manual Review"}
                </strong>
                <small>Authorized human verification remains available</small>
              </div>
            </div>
          </section>

          <section className="results-disclaimer">
            <div className="shield">🛡</div>

            <div>
              <h3>Explainable Decision-Support</h3>

              <p>
                DocShield provides an evidence-based screening recommendation.
                A high-risk or manual-review result indicates document
                indicators requiring further verification. It does not
                establish fraud or legally authenticate the document. Final
                decisions remain with the authorized human verifier.
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
          <p>DocShield-SIH2026 • Explainable Document Screening Prototype</p>
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
          <div className="hero-badge">SIH 2026 • MHA</div>

          <h1>
            Screen Documents.
            <span> Understand Risk.</span>
          </h1>

          <p>
            Upload a submitted document and compare it against an authorized
            reference already stored in DocShield. Our evidence-based pipeline
            combines OCR consistency, visual comparison, tamper indicators and
            document rules.
          </p>
        </section>

        <section className="workflow">
          <div className="step active">
            <span>1</span>
            Reference Loaded
          </div>

          <div className="line"></div>

          <div className={`step ${submittedFile ? "active" : ""}`}>
            <span>2</span>
            Upload Document
          </div>

          <div className="line"></div>

          <div className={`step ${isAnalyzing ? "active" : ""}`}>
            <span>3</span>
            Analyze Evidence
          </div>

          <div className="line"></div>

          <div className={`step ${analysisComplete ? "active" : ""}`}>
            <span>4</span>
            Review Risk
          </div>
        </section>

        <section className="comparison-layout">
          <div className="reference-card">
            <div className="reference-header">
              <div className="icon-box blue">✓</div>

              <div>
                <span className="card-label">AUTHORIZED REFERENCE</span>
                <h3>Reference Document</h3>
              </div>
            </div>

            <div className="reference-status">
              <span className="status-check">✓</span>

              <div>
                <strong>Reference Available</strong>
                <p>Loaded automatically from secure repository</p>
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
                <strong className="verified">Verified Reference</strong>
              </div>
            </div>

            <div className="repository-note">
              <span>◉</span>
              Authorized reference stored locally for prototype
            </div>
          </div>

          <div className="upload-card">
            <div className="card-top">
              <div className="icon-box orange">🔍</div>

              <div>
                <span className="card-label">DOCUMENT TO SCREEN</span>
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

            <div className="demo-mode">
              <div>
                <span>DEMO MODE</span>
                <p>
                  Temporary scenario selector. This will be replaced by the
                  backend result after integration.
                </p>
              </div>

              <select
                value={demoMode}
                onChange={(event) => setDemoMode(event.target.value)}
                disabled={isAnalyzing}
              >
                <option value="clear">Genuine — CLEAR</option>
                <option value="review">Modified — MANUAL REVIEW</option>
                <option value="high">Tampered — HIGH RISK</option>
              </select>
            </div>
          </div>
        </section>

        <section className="pipeline">
          <div className="pipeline-heading">
            <span className="section-label">ANALYSIS PIPELINE</span>

            <h2>
              Reference <span>vs</span> Submitted Document
            </h2>

            <p>
              DocShield evaluates multiple independent evidence signals before
              generating a screening recommendation.
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
                <span className="section-label">LIVE ANALYSIS</span>

                <h2>Analyzing Submitted Document</h2>

                <p>
                  DocShield is evaluating the document against the authorized
                  reference.
                </p>
              </div>

              <div className="analysis-spinner"></div>
            </div>

            <div className="analysis-steps">
              {analysisSteps.map((step, index) => {
                const isComplete = index < currentStep;
                const isCurrent = index === currentStep;

                return (
                  <div
                    className={`analysis-step ${
                      isComplete ? "complete" : ""
                    } ${isCurrent ? "current" : ""}`}
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

                      {isCurrent && <span className="mini-spinner"></span>}
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
                    ((currentStep + 1) / analysisSteps.length) * 100
                  )}%`,
                }}
              ></div>
            </div>

            <p className="analysis-note">
              Processing locally for prototype demonstration.
            </p>
          </section>
        )}

        {analysisComplete && (
          <section className="analysis-complete">
            <div className="complete-icon">✓</div>

            <div>
              <span className="section-label">ANALYSIS COMPLETE</span>

              <h2>Evidence analysis finished successfully</h2>

              <p>
                The document has passed through OCR, reference comparison,
                tamper analysis, document rules and the risk assessment stage.
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
              className={`analyze-btn ${submittedFile ? "enabled" : ""}`}
              disabled={!submittedFile}
              onClick={handleAnalyze}
              type="button"
            >
              Analyze Submitted Document
              <span>→</span>
            </button>

            <p>
              The authorized reference will be automatically used for
              comparison.
            </p>
          </section>
        )}

        {analysisComplete && (
          <div className="reset-container">
            <button className="reset-btn" onClick={handleReset} type="button">
              Analyze Another Document
            </button>
          </div>
        )}

        <section className="disclaimer">
          <div className="shield">🛡</div>

          <div>
            <h3>Decision-Support System</h3>

            <p>
              DocShield is an AI-assisted screening tool. A high-risk result
              indicates document indicators requiring further verification. It
              does not establish fraud or provide legally binding
              authentication. Final verification remains with the authorized
              human officer.
            </p>
          </div>
        </section>
      </main>

      <footer>
        <p>DocShield-SIH2026 • Smart India Hackathon Prototype</p>
      </footer>
    </div>
  );
}

export default App;