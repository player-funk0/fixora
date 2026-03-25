import { useState } from "react";
import { LANGUAGES } from "../constants.js";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button className="copy-btn" onClick={handle}>
      {copied ? "✓ Copied" : "Copy"}
    </button>
  );
}

export default function ResultsPanel({ result, loading, error, language, learningMode }) {
  const errCount  = result?.errors?.filter((e) => e.type === "error").length   ?? 0;
  const warnCount = result?.errors?.filter((e) => e.type === "warning").length ?? 0;
  const langLabel = LANGUAGES.find((l) => l.value === language)?.label ?? language;

  return (
    <div className="fx-panel" style={{ minHeight: "100%" }}>
      <div className="fx-panel-header">
        <span className="fx-panel-title">// analysis results</span>
        {result && (
          <span
            className="fx-badge"
            style={{
              background:  errCount > 0 ? "rgba(255,60,60,0.1)"  : "rgba(0,255,180,0.1)",
              borderColor: errCount > 0 ? "rgba(255,60,60,0.3)"  : "rgba(0,255,180,0.3)",
              color:       errCount > 0 ? "#ff8f8f"              : "#00ffb4",
            }}
          >
            {errCount > 0 ? `${errCount} error${errCount !== 1 ? "s" : ""}` : "✓ Clean"}
          </span>
        )}
      </div>

      <div className="fx-results-body">
        {/* Empty state */}
        {!result && !error && !loading && (
          <div className="fx-empty">
            <span style={{ fontSize: "2.5rem", opacity: 0.2 }}>🔍</span>
            <p>Submit code to see analysis</p>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="fx-empty">
            <span style={{ fontSize: "2rem", animation: "spin 1.2s linear infinite", display: "inline-block" }}>⚙️</span>
            <p>AI is reading your code…</p>
          </div>
        )}

        {/* Global error */}
        {error && !loading && (
          <div className="global-err">{error}</div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            {/* Stats row */}
            <div className="fx-summary">
              <div className={`fx-stat ${errCount > 0 ? "bad" : ""}`}>
                <div className="fx-stat-num">{errCount}</div>
                <div className="fx-stat-label">Errors</div>
              </div>
              <div className={`fx-stat ${warnCount > 0 ? "warn" : ""}`}>
                <div className="fx-stat-num">{warnCount}</div>
                <div className="fx-stat-label">Warnings</div>
              </div>
              <div className="fx-stat" style={{ flex: 3, textAlign: "left" }}>
                <div className="summary-text">{result.summary}</div>
                {result._meta && (
                  <div className="summary-meta">
                    {result._meta.response_ms}ms ·{" "}
                    {result._meta.used}/
                    {result._meta.limit === -1 ? "∞" : result._meta.limit} today
                  </div>
                )}
              </div>
            </div>

            {/* Issues */}
            {result.errors?.length > 0 && (
              <div>
                <div className="fx-section-title">Issues Found</div>
                {result.errors.map((err, i) => (
                  <div
                    key={i}
                    className={`fx-error-card ${err.type === "warning" ? "warning" : ""}`}
                    style={{ animationDelay: `${i * 0.07}s`, marginBottom: 10 }}
                  >
                    <div className="fx-error-line">
                      {err.type === "warning" ? "⚠ WARNING" : "✗ ERROR"}
                      {err.line ? ` · Line ${err.line}` : ""}
                    </div>
                    <div className="fx-error-msg">{err.title}</div>
                    <div className="fx-error-explain">{err.explanation}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Clean code */}
            {result.errors?.length === 0 && (
              <div className="fx-error-card hint">
                <div className="fx-error-line">✓ NO ISSUES</div>
                <div className="fx-error-msg">Your code looks great!</div>
                <div className="fx-error-explain">
                  No syntax, logic, or runtime errors detected.
                </div>
              </div>
            )}

            {/* Learning hints */}
            {learningMode && result.hints?.length > 0 && (
              <div>
                <div className="fx-section-title">Learning Hints</div>
                <div className="hint-box">
                  <div className="hint-box-title">🎓 Think it through</div>
                  {result.hints.map((hint, i) => (
                    <p key={i} className="hint-step">
                      <strong className="hint-step-label">Step {i + 1} →</strong>{" "}
                      {hint}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Corrected code */}
            {!learningMode && result.correctedCode && (
              <div>
                <div className="fx-section-title">Corrected Code</div>
                <div className="code-block">
                  <div className="code-block-header">
                    <span className="code-block-title">
                      ✓ Fixed · {langLabel}
                    </span>
                    <CopyButton text={result.correctedCode} />
                  </div>
                  <pre className="code-pre">{result.correctedCode}</pre>
                </div>
              </div>
            )}

            {learningMode && (
              <p className="learning-hint-footer">
                💡 Disable Learning Mode to reveal the corrected code
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
