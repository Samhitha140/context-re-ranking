import { useState, useCallback } from "react";
import "./App.css";

const API = "http://localhost:5050";

const PERSONAS = {
  Student:    { icon: "🎓", color: "#4F7FFF", bg: "#EEF2FF", desc: "Tutorials & learning" },
  Researcher: { icon: "🔬", color: "#7C3AED", bg: "#F5F3FF", desc: "Papers & citations" },
  Developer:  { icon: "💻", color: "#059669", bg: "#ECFDF5", desc: "Code & docs" },
  Journalist: { icon: "📰", color: "#D97706", bg: "#FFFBEB", desc: "News & facts" },
  Business:   { icon: "📊", color: "#DC2626", bg: "#FEF2F2", desc: "Strategy & markets" },
  Casual:     { icon: "🌐", color: "#6B7280", bg: "#F9FAFB", desc: "General browsing" },
  Medical:    { icon: "⚕️", color: "#0891B2", bg: "#ECFEFF", desc: "Healthcare" },
  Legal:      { icon: "⚖️", color: "#92400E", bg: "#FEF3C7", desc: "Laws & regulations" },
};

const FEATURES = {
  tfidf:          { label: "TF-IDF",           color: "#4F7FFF" },
  semantic:       { label: "Semantic",          color: "#7C3AED" },
  freshness:      { label: "Freshness",         color: "#059669" },
  title_match:    { label: "Title Match",       color: "#D97706" },
  snippet_depth:  { label: "Snippet Depth",     color: "#DC2626" },
  keyword_density:{ label: "Keyword Density",   color: "#0891B2" },
  persona_match:  { label: "Persona Match",     color: "#92400E" },
  domain_boost:   { label: "Domain Boost",      color: "#16A34A" },
};

const INTENT_META = {
  tool:     { label: "Tool Search",    icon: "🔧", color: "#059669", bg: "#ECFDF5" },
  learn:    { label: "Learning",       icon: "📚", color: "#4F7FFF", bg: "#EEF2FF" },
  fix:      { label: "Troubleshoot",   icon: "🐛", color: "#DC2626", bg: "#FEF2F2" },
  research: { label: "Research",       icon: "🔬", color: "#7C3AED", bg: "#F5F3FF" },
  news:     { label: "News & Updates", icon: "📰", color: "#D97706", bg: "#FFFBEB" },
  compare:  { label: "Comparison",     icon: "⚖️", color: "#0891B2", bg: "#ECFEFF" },
  general:  { label: "General",        icon: "🌐", color: "#6B7280", bg: "#F9FAFB" },
};

const SUGGESTIONS = [
  "free AI tools for students",
  "Python error fix tutorial",
  "latest NLP research papers 2025",
  "JavaScript vs TypeScript comparison",
  "treatment for anxiety symptoms",
  "startup fundraising strategies",
];

// ── Primitives ────────────────────────────────────────────────────────────────
function ScoreBar({ value, color, width = 80 }) {
  return (
    <div className="cr-bar">
      <div className="cr-bar-track" style={{ width }}>
        <div className="cr-bar-fill" style={{ width: `${Math.round(value * 100)}%`, background: color }} />
      </div>
      <span className="cr-bar-pct">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

function Delta({ delta }) {
  if (delta === 0) return <span className="cr-delta cr-delta-flat">—</span>;
  return (
    <span className={`cr-delta ${delta > 0 ? "cr-delta-up" : "cr-delta-down"}`}>
      {delta > 0 ? `↑${delta}` : `↓${Math.abs(delta)}`}
    </span>
  );
}

// ── Result card ───────────────────────────────────────────────────────────────
function ResultCard({ result, rank, open, onToggle }) {
  const domain = (() => {
    try { return new URL(result.url).hostname.replace("www.", ""); }
    catch { return result.url; }
  })();
  const f = result.features || {};
  const boosted = (f.domain_boost || 0) > 0;
  const top3 = rank <= 3;

  return (
    <div className={`cr-card ${open ? "open" : ""}`}>
      <div className="cr-card-top" onClick={onToggle}>
        {/* Rank badge */}
        <div className="cr-rank" style={{
          background: top3 ? "#EEF2FF" : "#F8FAFC",
          color:      top3 ? "#4F7FFF" : "#94A3B8",
        }}>
          {rank}
        </div>

        {/* Main content */}
        <div className="cr-card-body">
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="cr-card-title"
            onClick={e => e.stopPropagation()}
          >
            {result.title}
          </a>
          <div className="cr-card-domain">
            {domain}
            {boosted && <span className="cr-boost-dot" title="Domain boost applied" />}
          </div>
          <div className="cr-card-snippet">{result.snippet}</div>
          <ScoreBar value={result.composite_score || 0} color="#6366F1" width={150} />
        </div>

        {/* Score */}
        <div className="cr-card-right">
          <div className="cr-score-big">
            {((result.composite_score || 0) * 100).toFixed(0)}
            <span className="cr-score-unit">pts</span>
          </div>
          <Delta delta={result.rank_delta || 0} />
          <span className="cr-was">was #{result.original_rank}</span>
        </div>
      </div>

      {open && (
        <div className="cr-breakdown">
          <div className="cr-breakdown-title">8-Feature Breakdown</div>
          <div className="cr-breakdown-grid">
            {Object.entries(FEATURES).map(([key, { label, color }]) => (
              <div key={key} className="cr-feat-row">
                <span className="cr-feat-key">{label}</span>
                <ScoreBar value={f[key] || 0} color={color} width={90} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Weight chart ──────────────────────────────────────────────────────────────
function WeightChart({ weights, persona }) {
  const p = PERSONAS[persona];
  const entries = Object.entries(weights);
  const max = Math.max(...entries.map(([, v]) => v));
  return (
    <div className="cr-weight-card">
      <div className="cr-weight-top">
        <span className="cr-weight-icon">{p.icon}</span>
        <div>
          <div className="cr-weight-pname" style={{ color: p.color }}>{persona} Profile</div>
          <div className="cr-weight-pdesc">Effective feature weights for this query</div>
        </div>
      </div>
      {entries.map(([key, val]) => (
        <div key={key} className="cr-weight-row">
          <span className="cr-weight-key">{FEATURES[key]?.label || key}</span>
          <div className="cr-weight-track">
            <div className="cr-weight-fill" style={{
              width: `${(val / max) * 100}%`,
              background: FEATURES[key]?.color || "#6366F1",
            }} />
          </div>
          <span className="cr-weight-val">{(val * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}

// ── Feature map table ─────────────────────────────────────────────────────────
function FeatureTable({ results }) {
  return (
    <div className="cr-table-card">
      <div className="cr-table-head">Feature Scores — All Results</div>
      <div className="cr-table-scroll">
        <table className="cr-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Title</th>
              {Object.values(FEATURES).map(({ label }) => <th key={label}>{label}</th>)}
              <th style={{ color: "#6366F1" }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 700, color: i < 3 ? "#6366F1" : "#94A3B8" }}>#{i + 1}</td>
                <td title={r.title}>{r.title.substring(0, 38)}{r.title.length > 38 ? "…" : ""}</td>
                {Object.keys(FEATURES).map(k => {
                  const pct = Math.round((r.features?.[k] || 0) * 100);
                  return (
                    <td key={k}>
                      <span style={{
                        display: "inline-block", padding: "2px 6px", borderRadius: 4, fontWeight: 600, fontSize: 11,
                        background: pct > 70 ? "#ECFDF5" : pct > 40 ? "#EEF2FF" : "#F9FAFB",
                        color:      pct > 70 ? "#059669" : pct > 40 ? "#4F7FFF" : "#9CA3AF",
                      }}>{pct}</span>
                    </td>
                  );
                })}
                <td style={{ fontWeight: 700, color: "#0F172A" }}>
                  {Math.round((r.composite_score || 0) * 100)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function ContextRank() {
  const [query,       setQuery]       = useState("");
  const [persona,     setPersona]     = useState("Student");
  const [results,     setResults]     = useState([]);
  const [meta,        setMeta]        = useState(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState("");
  const [openIdx,     setOpenIdx]     = useState(null);
  const [tab,         setTab]         = useState("results");
  const [useDemo,     setUseDemo]     = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

  const search = useCallback(async (override) => {
    const q = (override ?? query).trim();
    if (!q) return;
    setLoading(true);
    setError("");
    setOpenIdx(null);
    try {
      const res = await fetch(`${API}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, persona, use_demo: useDemo }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setResults(data.results);
      setMeta(data.meta);
      setHasSearched(true);
      setTab("results");
    } catch (err) {
      setError("Search failed: " + err.message + " — is the Flask server running on port 5050?");
    }
    setLoading(false);
  }, [query, persona, useDemo]);

  const p  = PERSONAS[persona];
  const im = meta?.intent ? (INTENT_META[meta.intent] || INTENT_META.general) : null;

  return (
    <div className="cr-app">

      {/* ── Sidebar ── */}
      <aside className="cr-sidebar">
        <div className="cr-logo">
          <div className="cr-logo-mark">🎯</div>
          <div className="cr-logo-title">ContextRank</div>
          <div className="cr-logo-sub">Personalised Search Re-Ranking Engine</div>
          <div className="cr-tech-tags">
            {["Sentence-BERT", "TF-IDF", "Intent Detection"].map(t => (
              <span key={t} className="cr-tech-tag">{t}</span>
            ))}
          </div>
        </div>

        <div className="cr-section-label">Your Profile</div>
        <div className="cr-persona-list">
          {Object.entries(PERSONAS).map(([name, info]) => (
            <button
              key={name}
              className={`cr-persona-item ${persona === name ? "active" : ""}`}
              style={{ "--p-color": info.color, "--p-bg": info.bg }}
              onClick={() => setPersona(name)}
            >
              <span className="cr-persona-icon">{info.icon}</span>
              <span>
                <span className="cr-persona-name">{name}</span>
                <span className="cr-persona-desc">{info.desc}</span>
              </span>
            </button>
          ))}
        </div>

        <div className="cr-sidebar-footer">
          <div className="cr-mode-row">
            <span className={`cr-mode-label ${useDemo ? "on" : ""}`}>Demo</span>
            <div
              className="cr-toggle"
              style={{ background: useDemo ? "#CBD5E1" : "#6366F1" }}
              onClick={() => setUseDemo(d => !d)}
            >
              <div className="cr-toggle-knob" style={{ left: useDemo ? 2 : 18 }} />
            </div>
            <span className={`cr-mode-label ${!useDemo ? "on" : ""}`}>Live</span>
          </div>
          <div className="cr-mode-hint">
            {useDemo ? "Uses built-in demo corpus" : "Live DuckDuckGo search"}
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="cr-main">

        {/* Search strip */}
        <div className="cr-search-strip">
          <div className="cr-active-pill" style={{ background: p.bg, color: p.color }}>
            {p.icon} Searching as {persona}
          </div>
          <div className="cr-search-row">
            <div className="cr-search-wrap">
              <span className="cr-search-icon">🔍</span>
              <input
                className="cr-search-input"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === "Enter" && search()}
                placeholder={`What are you looking for, ${persona.toLowerCase()}?`}
              />
            </div>
            <button className="cr-search-btn" onClick={() => search()} disabled={loading || !query.trim()}>
              {loading ? "Ranking…" : "Re-Rank"}
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="cr-content">

          {error && <div className="cr-error">⚠️ {error}</div>}

          {loading && (
            <div className="cr-loading">
              <div className="cr-spinner" />
              <div className="cr-loading-title">Running 8-Feature Pipeline…</div>
              <div className="cr-loading-sub">TF-IDF · Sentence-BERT · Intent Detection · Persona Matching</div>
            </div>
          )}

          {!loading && hasSearched && results.length > 0 && (
            <>
              {/* Intent badge */}
              {im && (
                <div className="cr-intent-row">
                  <span className="cr-intent-label">Detected intent:</span>
                  <span className="cr-intent-badge" style={{ background: im.bg, color: im.color }}>
                    {im.icon} {im.label}
                  </span>
                  <span className="cr-intent-note">domain boosts & weights adjusted</span>
                </div>
              )}

              {/* Stats */}
              <div className="cr-stats">
                {[
                  { key: "Results",     val: meta?.total ?? 0 },
                  { key: "Avg Score",   val: `${((meta?.avg_composite_score ?? 0) * 100).toFixed(0)}%` },
                  { key: "Moved Up",    val: meta?.moved_up ?? 0,   color: "#059669" },
                  { key: "Moved Down",  val: meta?.moved_down ?? 0, color: "#DC2626" },
                  { key: "Rank Time",   val: `${meta?.rank_ms ?? 0}ms` },
                ].map(s => (
                  <div key={s.key} className="cr-stat">
                    <div className="cr-stat-key">{s.key}</div>
                    <div className="cr-stat-val" style={{ color: s.color || "#0F172A" }}>{s.val}</div>
                  </div>
                ))}
              </div>

              {/* Tabs */}
              <div className="cr-tabs">
                {[
                  { id: "results", label: "Results" },
                  { id: "weights", label: "Weights" },
                  { id: "table",   label: "Feature Map" },
                ].map(t => (
                  <button key={t.id} className={`cr-tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
                    {t.label}
                  </button>
                ))}
              </div>

              {tab === "results" && (
                <div className="cr-results">
                  {results.map((r, i) => (
                    <ResultCard
                      key={i} result={r} rank={i + 1}
                      open={openIdx === i}
                      onToggle={() => setOpenIdx(openIdx === i ? null : i)}
                    />
                  ))}
                </div>
              )}

              {tab === "weights" && meta?.weights && (
                <WeightChart weights={meta.weights} persona={persona} />
              )}

              {tab === "table" && <FeatureTable results={results} />}
            </>
          )}

          {!loading && !hasSearched && (
            <div className="cr-empty">
              <div className="cr-empty-icon">🎯</div>
              <div className="cr-empty-title">Personalised Search Re-Ranking</div>
              <div className="cr-empty-desc">
                Pick your profile from the sidebar, type a query, and hit Re-Rank.
                The 8-feature ML pipeline re-orders results using intent detection,
                Sentence-BERT embeddings, and persona-weighted scoring.
              </div>
              <div className="cr-chips">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    className="cr-chip"
                    onClick={() => { setQuery(s); search(s); }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
