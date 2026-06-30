import { useState, useCallback } from "react";

const API = "http://localhost:5050";

const PERSONAS = {
  Student:    { icon: "🎓", color: "#4F7FFF", bg: "#EEF2FF", desc: "Tutorials & explanations" },
  Researcher: { icon: "🔬", color: "#7C3AED", bg: "#F5F3FF", desc: "Papers & citations" },
  Developer:  { icon: "💻", color: "#059669", bg: "#ECFDF5", desc: "Code & documentation" },
  Journalist: { icon: "📰", color: "#D97706", bg: "#FFFBEB", desc: "News & facts" },
  Business:   { icon: "📊", color: "#DC2626", bg: "#FEF2F2", desc: "Strategy & market insights" },
  Casual:     { icon: "🌐", color: "#6B7280", bg: "#F9FAFB", desc: "General browsing" },
  Medical:    { icon: "⚕️", color: "#0891B2", bg: "#ECFEFF", desc: "Healthcare info" },
  Legal:      { icon: "⚖️", color: "#92400E", bg: "#FEF3C7", desc: "Laws & regulations" },
};

const FEATURE_LABELS = {
  tfidf: "TF-IDF",
  semantic: "Semantic",
  freshness: "Freshness",
  title_match: "Title Match",
  snippet_depth: "Snippet Depth",
  keyword_density: "Keyword Density",
  persona_match: "Persona Match",
  domain_boost: "Domain Boost",
};

const FEATURE_COLORS = {
  tfidf: "#4F7FFF",
  semantic: "#7C3AED",
  freshness: "#059669",
  title_match: "#D97706",
  snippet_depth: "#DC2626",
  keyword_density: "#0891B2",
  persona_match: "#92400E",
  domain_boost: "#16A34A",
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

function ScoreBar({ value, color, width = 60 }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width, height: 6, background: "#F3F4F6", borderRadius: 99, overflow: "hidden" }}>
        <div style={{ width: `${Math.round(value * 100)}%`, height: "100%", background: color, borderRadius: 99, transition: "width 0.5s ease" }} />
      </div>
      <span style={{ fontSize: 11, color: "#9CA3AF", minWidth: 28 }}>{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

function RankBadge({ delta }) {
  if (delta === 0) return <span style={{ fontSize: 11, color: "#9CA3AF", padding: "2px 6px", background: "#F9FAFB", borderRadius: 4 }}>—</span>;
  const up = delta > 0;
  return (
    <span style={{ fontSize: 11, fontWeight: 600, color: up ? "#059669" : "#DC2626", padding: "2px 6px", background: up ? "#ECFDF5" : "#FEF2F2", borderRadius: 4 }}>
      {up ? `↑${delta}` : `↓${Math.abs(delta)}`}
    </span>
  );
}

function ResultCard({ result, rank, expanded, onToggle }) {
  const domain = (() => { try { return new URL(result.url).hostname.replace("www.", ""); } catch { return result.url; } })();
  const features = result.features || {};

  return (
    <div style={{
      background: "#fff", border: "1px solid #E5E7EB", borderRadius: 12, overflow: "hidden",
      transition: "box-shadow 0.2s", boxShadow: expanded ? "0 4px 20px rgba(0,0,0,0.08)" : "none",
    }}>
      <div style={{ padding: "14px 16px", cursor: "pointer" }} onClick={onToggle}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{
            minWidth: 32, height: 32, borderRadius: 8,
            background: rank <= 3 ? "#EEF2FF" : "#F9FAFB",
            color: rank <= 3 ? "#4F7FFF" : "#9CA3AF",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14, fontWeight: 700, flexShrink: 0,
          }}>{rank}</div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
              <a href={result.url} target="_blank" rel="noopener noreferrer"
                onClick={e => e.stopPropagation()}
                style={{ fontSize: 14, fontWeight: 600, color: "#1E40AF", textDecoration: "none", lineHeight: 1.3 }}
                onMouseOver={e => e.target.style.textDecoration = "underline"}
                onMouseOut={e => e.target.style.textDecoration = "none"}
              >{result.title}</a>
            </div>
            <div style={{ fontSize: 11, color: "#6B7280", marginBottom: 6 }}>{domain}</div>
            <div style={{ fontSize: 13, color: "#4B5563", lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
              {result.snippet}
            </div>
          </div>

          <div style={{ flexShrink: 0, textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: "#111827" }}>
              {((result.composite_score || 0) * 100).toFixed(0)}
              <span style={{ fontSize: 10, fontWeight: 400, color: "#9CA3AF" }}>pts</span>
            </div>
            <RankBadge delta={result.rank_delta || 0} />
            <div style={{ fontSize: 10, color: "#D1D5DB" }}>was #{result.original_rank}</div>
          </div>
        </div>
        <div style={{ marginTop: 10, marginLeft: 44 }}>
          <ScoreBar value={result.composite_score || 0} color="#4F7FFF" width={120} />
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: "1px solid #F3F4F6", padding: "12px 16px 14px 60px", background: "#FAFAFA" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "#9CA3AF", letterSpacing: "0.05em", marginBottom: 10 }}>7-FEATURE BREAKDOWN</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "8px 20px" }}>
            {Object.entries(FEATURE_LABELS).map(([key, label]) => (
              <div key={key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                <span style={{ fontSize: 12, color: "#6B7280", minWidth: 100 }}>{label}</span>
                <ScoreBar value={features[key] || 0} color={FEATURE_COLORS[key]} width={80} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PersonaCard({ name, selected, onClick }) {
  const p = PERSONAS[name];
  return (
    <div onClick={onClick} style={{
      padding: "10px 14px", borderRadius: 10, cursor: "pointer",
      border: selected ? `2px solid ${p.color}` : "1.5px solid #E5E7EB",
      background: selected ? p.bg : "#fff", transition: "all 0.15s",
      display: "flex", alignItems: "center", gap: 10,
    }}>
      <span style={{ fontSize: 20 }}>{p.icon}</span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: selected ? p.color : "#374151" }}>{name}</div>
        <div style={{ fontSize: 11, color: "#9CA3AF" }}>{p.desc}</div>
      </div>
    </div>
  );
}

function WeightChart({ weights }) {
  const entries = Object.entries(weights);
  const maxW = Math.max(...entries.map(([, v]) => v));
  return (
    <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 12, padding: "16px" }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: "#9CA3AF", letterSpacing: "0.05em", marginBottom: 12 }}>PERSONA WEIGHT DISTRIBUTION</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {entries.map(([key, val]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 12, color: "#6B7280", width: 120, flexShrink: 0 }}>{FEATURE_LABELS[key] || key}</span>
            <div style={{ flex: 1, height: 8, background: "#F3F4F6", borderRadius: 99 }}>
              <div style={{ width: `${(val / maxW) * 100}%`, height: "100%", background: FEATURE_COLORS[key] || "#4F7FFF", borderRadius: 99, transition: "width 0.6s ease" }} />
            </div>
            <span style={{ fontSize: 11, color: "#9CA3AF", width: 34, textAlign: "right" }}>{(val * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ContextRank() {
  const [query, setQuery] = useState("");
  const [persona, setPersona] = useState("Student");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState(null);
  const [tab, setTab] = useState("results");
  const [useDemo, setUseDemo] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), persona, use_demo: useDemo }),
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

  const p = PERSONAS[persona];

  return (
    <div style={{ fontFamily: "'DM Sans', system-ui, sans-serif", maxWidth: 900, margin: "0 auto", padding: "0 0 60px" }}>

      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F1A35 100%)",
        borderRadius: "0 0 24px 24px", padding: "32px 28px 28px", marginBottom: 24,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: "linear-gradient(135deg, #4F7FFF, #7C3AED)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20,
          }}>🎯</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#fff" }}>ContextRank</h1>
            <div style={{ fontSize: 12, color: "#94A3B8" }}>Personalised Search Re-Ranking Engine</div>
          </div>

          {/* Demo / Live toggle */}
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "#94A3B8" }}>Demo</span>
            <div onClick={() => setUseDemo(d => !d)} style={{
              width: 40, height: 22, borderRadius: 99, cursor: "pointer",
              background: useDemo ? "#334155" : "#4F7FFF", position: "relative", transition: "background 0.2s",
            }}>
              <div style={{
                position: "absolute", top: 3, left: useDemo ? 3 : 19,
                width: 16, height: 16, borderRadius: "50%", background: "#fff", transition: "left 0.2s",
              }} />
            </div>
            <span style={{ fontSize: 12, color: "#94A3B8" }}>Live</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
          {["TF-IDF", "Sentence-BERT", "7-Feature Pipeline", "8 Persona Profiles", "Cosine Similarity"].map(tag => (
            <span key={tag} style={{
              fontSize: 11, padding: "3px 8px", borderRadius: 4, fontWeight: 500,
              background: "rgba(255,255,255,0.08)", color: "#94A3B8", border: "1px solid rgba(255,255,255,0.1)",
            }}>{tag}</span>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Enter your search query…"
            style={{
              flex: 1, padding: "12px 16px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)",
              background: "rgba(255,255,255,0.08)", color: "#fff", fontSize: 15, outline: "none",
            }}
          />
          <button onClick={handleSearch} disabled={loading || !query.trim()} style={{
            padding: "12px 24px", borderRadius: 10, border: "none",
            background: loading ? "#334155" : "linear-gradient(135deg, #4F7FFF, #7C3AED)",
            color: "#fff", fontSize: 15, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.2s", whiteSpace: "nowrap",
          }}>
            {loading ? "Ranking…" : "🔍 Re-Rank"}
          </button>
        </div>
      </div>

      <div style={{ padding: "0 16px" }}>
        {/* Persona selector */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#9CA3AF", letterSpacing: "0.05em", marginBottom: 10 }}>SELECT PERSONA</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 8 }}>
            {Object.keys(PERSONAS).map(name => (
              <PersonaCard key={name} name={name} selected={persona === name} onClick={() => setPersona(name)} />
            ))}
          </div>
        </div>

        {error && (
          <div style={{ padding: 12, background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 10, color: "#DC2626", fontSize: 13, marginBottom: 16 }}>
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", padding: 48 }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⚙️</div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#374151", marginBottom: 6 }}>Running 7-Feature Pipeline…</div>
            <div style={{ fontSize: 13, color: "#9CA3AF" }}>TF-IDF · Sentence-BERT · Cosine Similarity · Persona Matching</div>
          </div>
        )}

        {!loading && hasSearched && results.length > 0 && (
          <>
            {/* Intent badge */}
            {meta?.intent && (() => {
              const im = INTENT_META[meta.intent] || INTENT_META.general;
              return (
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                  <span style={{ fontSize: 12, color: "#9CA3AF" }}>Detected intent:</span>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 5,
                    padding: "4px 10px", borderRadius: 20,
                    background: im.bg, color: im.color,
                    fontSize: 12, fontWeight: 600, border: `1px solid ${im.color}22`,
                  }}>
                    {im.icon} {im.label}
                  </span>
                  <span style={{ fontSize: 11, color: "#9CA3AF" }}>— domain boosts & weights adjusted accordingly</span>
                </div>
              );
            })()}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10, marginBottom: 16 }}>
              {[
                { label: "Results",    value: meta?.total || 0,                                    icon: "📄" },
                { label: "Avg Score",  value: `${((meta?.avg_composite_score || 0) * 100).toFixed(0)}%`, icon: "📊" },
                { label: "Moved Up",   value: meta?.moved_up || 0,   icon: "↑", color: "#059669" },
                { label: "Moved Down", value: meta?.moved_down || 0, icon: "↓", color: "#DC2626" },
                { label: "Rank Time",  value: `${meta?.rank_ms || 0}ms`,       icon: "⚡" },
              ].map(s => (
                <div key={s.label} style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 10, padding: "10px 14px" }}>
                  <div style={{ fontSize: 11, color: "#9CA3AF", marginBottom: 4 }}>{s.icon} {s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color || "#111827" }}>{s.value}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", gap: 4, marginBottom: 16, background: "#F9FAFB", borderRadius: 10, padding: 4 }}>
              {["results", "weights", "compare"].map(t => (
                <button key={t} onClick={() => setTab(t)} style={{
                  flex: 1, padding: "8px 12px", borderRadius: 8, border: "none",
                  background: tab === t ? "#fff" : "transparent",
                  color: tab === t ? "#111827" : "#6B7280",
                  fontSize: 13, fontWeight: tab === t ? 600 : 400, cursor: "pointer",
                  boxShadow: tab === t ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                }}>
                  {t === "results" ? "🔢 Results" : t === "weights" ? "⚖️ Weights" : "📊 Feature Map"}
                </button>
              ))}
            </div>

            {tab === "results" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {results.map((r, i) => (
                  <ResultCard key={i} result={r} rank={i + 1}
                    expanded={expandedIdx === i}
                    onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}
                  />
                ))}
              </div>
            )}

            {tab === "weights" && meta?.weights && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <WeightChart weights={meta.weights} />
                <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 12, padding: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#9CA3AF", letterSpacing: "0.05em", marginBottom: 12 }}>PERSONA PROFILE: {persona.toUpperCase()}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                    <span style={{ fontSize: 32 }}>{p.icon}</span>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 600, color: p.color }}>{persona}</div>
                      <div style={{ fontSize: 13, color: "#6B7280" }}>{p.desc}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: "#4B5563", lineHeight: 1.6 }}>
                    This persona weights <strong>{Object.entries(meta.weights).sort((a, b) => b[1] - a[1])[0][0]}</strong> signals most heavily,
                    prioritising {
                      persona === "Researcher" ? "deep semantic similarity and academic sources" :
                      persona === "Developer"  ? "lexical code matching and technical documentation" :
                      persona === "Journalist" ? "content freshness and news sources" :
                      persona === "Student"    ? "semantic clarity and educational platforms" : "balanced relevance"
                    }.
                  </div>
                </div>
              </div>
            )}

            {tab === "compare" && (
              <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: 12, overflow: "hidden" }}>
                <div style={{ padding: "14px 16px", borderBottom: "1px solid #F3F4F6" }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#9CA3AF", letterSpacing: "0.05em" }}>FEATURE SCORES ACROSS TOP-10 RESULTS</div>
                </div>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                    <thead>
                      <tr style={{ background: "#F9FAFB" }}>
                        <th style={{ padding: "8px 12px", textAlign: "left", color: "#6B7280", fontWeight: 600 }}>Rank</th>
                        <th style={{ padding: "8px 12px", textAlign: "left", color: "#6B7280", fontWeight: 600 }}>Title</th>
                        {Object.values(FEATURE_LABELS).map(l => (
                          <th key={l} style={{ padding: "8px 8px", textAlign: "center", color: "#6B7280", fontWeight: 600, whiteSpace: "nowrap", fontSize: 11 }}>{l}</th>
                        ))}
                        <th style={{ padding: "8px 12px", textAlign: "center", color: "#4F7FFF", fontWeight: 600 }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((r, i) => (
                        <tr key={i} style={{ borderTop: "1px solid #F3F4F6", background: i % 2 === 0 ? "#fff" : "#FAFAFA" }}>
                          <td style={{ padding: "8px 12px", fontWeight: 700, color: i < 3 ? "#4F7FFF" : "#9CA3AF" }}>#{i + 1}</td>
                          <td style={{ padding: "8px 12px", maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#374151" }}>
                            {r.title.substring(0, 40)}…
                          </td>
                          {Object.keys(FEATURE_LABELS).map(k => {
                            const pct = Math.round((r.features?.[k] || 0) * 100);
                            return (
                              <td key={k} style={{ padding: "8px 8px", textAlign: "center" }}>
                                <div style={{
                                  display: "inline-block", padding: "2px 6px", borderRadius: 4,
                                  background: pct > 70 ? "#ECFDF5" : pct > 40 ? "#EEF2FF" : "#F9FAFB",
                                  color: pct > 70 ? "#059669" : pct > 40 ? "#4F7FFF" : "#9CA3AF",
                                  fontWeight: 600, fontSize: 11,
                                }}>{pct}</div>
                              </td>
                            );
                          })}
                          <td style={{ padding: "8px 12px", textAlign: "center", fontWeight: 700, color: "#111827" }}>
                            {Math.round((r.composite_score || 0) * 100)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {!loading && !hasSearched && (
          <div style={{ textAlign: "center", padding: "48px 24px" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: "#111827", margin: "0 0 8px" }}>Personalised Search Re-Ranking</h2>
            <p style={{ fontSize: 14, color: "#6B7280", maxWidth: 440, margin: "0 auto 24px", lineHeight: 1.6 }}>
              Enter a query and select a persona. The 7-feature ML pipeline will re-rank results using TF-IDF, Sentence-BERT embeddings, and persona-weighted cosine scoring.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
              {["machine learning NLP", "Python REST API tutorial", "latest AI research 2025", "treatment for diabetes"].map(q => (
                <button key={q} onClick={() => setQuery(q)} style={{
                  padding: "8px 14px", borderRadius: 8, border: "1px solid #E5E7EB",
                  background: "#fff", color: "#374151", fontSize: 13, cursor: "pointer",
                }}
                  onMouseOver={e => { e.currentTarget.style.background = "#F9FAFB"; }}
                  onMouseOut={e => { e.currentTarget.style.background = "#fff"; }}
                >{q}</button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
