export default function UsageBanner({ used, limit, onUpgrade }) {
  if (limit === -1) return null;           // unlimited plan — hide banner

  const pct  = Math.min((used / limit) * 100, 100);
  const full = used >= limit;
  const near = pct >= 80;

  return (
    <div className={`usage-banner ${near ? "near" : ""}`}>
      <div className="usage-banner-row">
        <span className="usage-label">DAILY USAGE</span>
        <span className={`usage-count ${near ? "warn" : ""}`}>
          {used} / {limit}
        </span>
      </div>

      <div className="usage-bar">
        <div
          className="usage-fill"
          style={{ width: `${pct}%`, background: near ? "#ffb400" : "#00ffb4" }}
        />
      </div>

      {near && (
        <div className="usage-cta">
          <span className="usage-cta-text">
            {full ? "Daily limit reached." : "Almost at your limit."}
          </span>
          <button className="upgrade-btn" onClick={onUpgrade}>
            Upgrade to Pro →
          </button>
        </div>
      )}
    </div>
  );
}
