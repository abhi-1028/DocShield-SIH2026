import { useState } from "react";
import "./App.css";

function App() {
  const [submittedFile, setSubmittedFile] = useState(null);

  const handleAnalyze = () => {
    if (!submittedFile) return;

    alert(
      "Document ready for analysis.\n\nNext step: Connect this button to the FastAPI /analyze endpoint."
    );
  };

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
        {/* HERO */}

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

        {/* WORKFLOW */}

        <section className="workflow">
          <div className="step active">
            <span>1</span>
            Reference Loaded
          </div>

          <div className="line"></div>

          <div className="step active">
            <span>2</span>
            Upload Document
          </div>

          <div className="line"></div>

          <div className="step">
            <span>3</span>
            Analyze Evidence
          </div>

          <div className="line"></div>

          <div className="step">
            <span>4</span>
            Review Risk
          </div>
        </section>

        {/* REFERENCE + SUBMISSION */}

        <section className="comparison-layout">
          {/* STORED REFERENCE */}

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

          {/* SUBMITTED DOCUMENT */}

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
                onChange={(e) => setSubmittedFile(e.target.files[0])}
              />

              <div className="upload-content">
                <div className="upload-icon">⇧</div>

                <h4>
                  {submittedFile
                    ? submittedFile.name
                    : "Upload submitted document"}
                </h4>

                <p>PNG, JPG or PDF</p>
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

        {/* ANALYSIS PIPELINE */}

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

        {/* ANALYZE */}

        <section className="analyze-section">
          <button
            className={`analyze-btn ${submittedFile ? "enabled" : ""}`}
            disabled={!submittedFile}
            onClick={handleAnalyze}
          >
            Analyze Submitted Document
            <span>→</span>
          </button>

          <p>
            The authorized reference will be automatically used for comparison.
          </p>
        </section>

        {/* DISCLAIMER */}

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