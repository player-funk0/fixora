import { useState } from "react";

export default function AuthModal({ api, onClose, onSuccess }) {
  const [tab,     setTab]     = useState("login");
  const [email,   setEmail]   = useState("");
  const [pass,    setPass]    = useState("");
  const [role,    setRole]    = useState("student");
  const [err,     setErr]     = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!email || !pass) { setErr("Email and password are required."); return; }
    setErr("");
    setLoading(true);
    try {
      const data =
        tab === "login"
          ? await api.post("/api/auth/login/",    { email, password: pass })
          : await api.post("/api/auth/register/", { email, password: pass, role });

      api.setToken(data.access);
      onSuccess({ email, plan: data.plan, role: data.role });
    } catch (e) {
      setErr(e.error || e.detail || e.email?.[0] || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>

        {/* Tabs */}
        <div className="modal-tabs">
          {["login", "register"].map((t) => (
            <button
              key={t}
              className={`modal-tab ${tab === t ? "active" : ""}`}
              onClick={() => { setTab(t); setErr(""); }}
            >
              {t === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        <div className="modal-body">
          <label className="field-label">Email</label>
          <input
            className="field-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />

          <label className="field-label" style={{ marginTop: 14 }}>Password</label>
          <input
            className="field-input"
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            placeholder="min. 6 characters"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />

          {tab === "register" && (
            <>
              <label className="field-label" style={{ marginTop: 14 }}>I am a…</label>
              <select
                className="field-select"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>
            </>
          )}

          {err && <div className="auth-err">{err}</div>}

          <button className="auth-submit-btn" onClick={submit} disabled={loading}>
            {loading ? "…" : tab === "login" ? "Sign In" : "Create Account"}
          </button>

          <button className="auth-cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
