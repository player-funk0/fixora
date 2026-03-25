import { useState, useEffect, useRef, useCallback } from "react";
import { useApi }       from "./api.js";
import { LANGUAGES, EXT_TO_LANGUAGE, SAMPLE_CODE } from "./constants.js";
import MonacoEditor from "./components/MonacoEditor.jsx";
import AuthModal    from "./components/AuthModal.jsx";
import UsageBanner  from "./components/UsageBanner.jsx";
import ResultsPanel from "./components/ResultsPanel.jsx";

export default function App() {
  const api = useApi();

  // ── Editor state ────────────────────────────────────────────────────────────
  const [code,         setCode]         = useState("");
  const [language,     setLanguage]     = useState("python");
  const [learningMode, setLearningMode] = useState(false);
  const [uploadName,   setUploadName]   = useState("");

  // ── Request state ───────────────────────────────────────────────────────────
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [apiError, setApiError] = useState(null);

  // ── Auth / usage state ──────────────────────────────────────────────────────
  const [user,     setUser]     = useState(null);
  const [usage,    setUsage]    = useState({ used: 0, limit: 5, plan: "free" });
  const [showAuth, setShowAuth] = useState(false);

  const fileRef = useRef(null);

  // Refresh usage whenever the token changes (login/logout)
  useEffect(() => {
    api.get("/api/usage/").then(setUsage).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api.token]);

  // ── Auth ────────────────────────────────────────────────────────────────────
  const handleAuthSuccess = ({ email, plan, role }) => {
    setUser({ email, plan, role });
    setShowAuth(false);
    api.get("/api/usage/").then(setUsage).catch(() => {});
  };

  const handleLogout = () => {
    api.setToken(null);
    setUser(null);
    setUsage({ used: 0, limit: 5, plan: "free" });
  };

  // ── File handling ───────────────────────────────────────────────────────────
  const handleFile = useCallback(async (file) => {
    if (!file) return;
    try {
      const text = await file.text();
      const ext  = ("." + file.name.split(".").pop()).toLowerCase();
      setCode(text);
      setUploadName(file.name);
      setResult(null);
      setApiError(null);
      if (EXT_TO_LANGUAGE[ext]) setLanguage(EXT_TO_LANGUAGE[ext]);
    } catch {
      setApiError("Could not read file — make sure it is valid UTF-8 text.");
    }
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const loadSample = () => {
    setCode(SAMPLE_CODE[language] ?? SAMPLE_CODE.python);
    setUploadName("");
    setResult(null);
    setApiError(null);
  };

  const clearUpload = () => {
    setUploadName("");
    setCode("");
  };

  // ── Analyze ──────────────────────────────────────────────────────────────────
  const analyze = useCallback(async () => {
    if (!code.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setApiError(null);

    try {
      let data;

      if (uploadName) {
        // Multipart upload — Django logs via_upload = True
        const fd = new FormData();
        fd.append("file",         new Blob([code], { type: "text/plain" }), uploadName);
        fd.append("language",     language);
        fd.append("learningMode", String(learningMode)); // backend _parse_bool handles "true"/"false"
        data = await api.postForm("/api/analyze/upload/", fd);
      } else {
        data = await api.post("/api/analyze/", {
          code,
          language,
          learningMode,   // native boolean for JSON path
        });
      }

      setResult(data);
      if (data._meta) {
        setUsage((u) => ({ ...u, used: data._meta.used, limit: data._meta.limit }));
      }
    } catch (e) {
      if (e.status === 429) {
        setApiError(e.message ?? "Daily limit reached. Upgrade to Pro for unlimited access.");
        setUsage((u) => ({
          ...u,
          used:  e.used  ?? u.used,
          limit: e.limit ?? u.limit,
        }));
      } else {
        setApiError(e.error ?? e.detail ?? "Analysis failed. Is the Django server running on port 8000?");
      }
    } finally {
      setLoading(false);
    }
  // Depend on stable primitives/memoized fns — not the api object itself,
  // which is a new reference every render and would cause unnecessary recreation.
  }, [code, language, learningMode, uploadName, loading, api.post, api.postForm]);

  const atLimit = usage.limit !== -1 && usage.used >= usage.limit;

  return (
    <>
      {showAuth && (
        <AuthModal
          api={api}
          onClose={() => setShowAuth(false)}
          onSuccess={handleAuthSuccess}
        />
      )}

      <div className="fx-root">

        {/* ── Header ── */}
        <header className="fx-header">
          <div className="fx-logo">
            <div className="fx-logo-dot" />
            Fixora
            <span className="fx-badge">AI · Django</span>
          </div>

          <div className="header-auth">
            {user ? (
              <>
                <span className="header-user-info">
                  {user.email} · <span style={{ color: "#00ffb4" }}>{usage.plan}</span>
                </span>
                <button className="header-btn" onClick={handleLogout}>Log out</button>
              </>
            ) : (
              <button className="header-btn primary" onClick={() => setShowAuth(true)}>
                Sign in
              </button>
            )}
          </div>
        </header>

        <main className="fx-main">

          {/* ── Hero ── */}
          <div className="fx-hero">
            <h1>Debug smarter.<br /><span>Learn faster.</span></h1>
            <p>Paste code or upload a file — Fixora finds the errors, explains them, and shows the fix.</p>
          </div>

          {/* ── Usage bar ── */}
          <div style={{ maxWidth: 640, margin: "0 auto 28px" }}>
            <UsageBanner
              used={usage.used}
              limit={usage.limit}
              onUpgrade={() => setShowAuth(true)}
            />
          </div>

          {/* ── Main grid ── */}
          <div className="fx-grid">

            {/* LEFT: Code input */}
            <div>
              <div className="fx-panel">

                <div className="fx-panel-header">
                  <span className="fx-panel-title">// code input</span>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="fx-sample-btn" onClick={loadSample}>Sample</button>
                    <button className="fx-sample-btn" onClick={() => fileRef.current?.click()}>
                      📁 Upload
                    </button>
                    <input
                      ref={fileRef}
                      type="file"
                      style={{ display: "none" }}
                      accept=".py,.js,.ts,.cpp,.c,.java,.go,.rs"
                      onChange={(e) => handleFile(e.target.files[0])}
                    />
                  </div>
                </div>

                {/* Drop zone — visible only when editor is empty */}
                {!code && (
                  <div className="drop-zone" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
                    <span style={{ fontSize: "1.5rem" }}>📂</span>
                    <span className="drop-zone-label">Drop a file here or click Upload</span>
                  </div>
                )}

                {/* Controls */}
                <div className="fx-controls">
                  <select
                    className="fx-select"
                    value={language}
                    onChange={(e) => { setLanguage(e.target.value); setUploadName(""); }}
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.value} value={l.value} style={{ background: "#0d0d12" }}>
                        {l.label}
                      </option>
                    ))}
                  </select>

                  {uploadName && (
                    <span className="upload-chip">
                      📄 {uploadName}
                      <button className="upload-chip-remove" onClick={clearUpload}>✕</button>
                    </span>
                  )}

                  <div className="fx-toggle-wrap" onClick={() => setLearningMode((m) => !m)}>
                    <span className="fx-toggle-label">🎓 Learn</span>
                    <div className={`fx-toggle ${learningMode ? "on" : ""}`} />
                  </div>
                </div>

                {/* Monaco editor + drag-and-drop overlay */}
                <div onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
                  <MonacoEditor value={code} onChange={setCode} language={language} />
                </div>

                <button
                  className={`fx-analyze-btn${loading ? " loading" : ""}`}
                  onClick={analyze}
                  disabled={loading || !code.trim() || atLimit}
                >
                  {loading
                    ? <><span className="fx-spinner" />Analyzing…</>
                    : atLimit
                      ? "Daily limit reached — Upgrade to continue"
                      : "⚡ Analyze Code"}
                </button>

              </div>
            </div>

            {/* RIGHT: Results */}
            <div>
              <ResultsPanel
                result={result}
                loading={loading}
                error={apiError}
                language={language}
                learningMode={learningMode}
              />
            </div>

          </div>
        </main>

        <footer className="fx-footer">
          FIXORA · DJANGO + MOCK AI · SQLITE ANALYTICS
        </footer>
      </div>
    </>
  );
}
