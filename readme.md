# ContextRank — Personalised Search Re-Ranking Engine

> A full-stack ML pipeline that re-ranks web search results in real time using an 8-feature scoring system, 8 user persona profiles, and query intent detection — all without training a custom model or using any paid API.

**Stack:** Python · Flask · Sentence-BERT · TF-IDF · Cosine Similarity · React · Vite

---

## Screenshots

### Application UI

![ContextRank UI — Persona Selector and Search](<img width="1911" height="875" alt="Screenshot 2026-06-30 172703" src="https://github.com/user-attachments/assets/6b2dc738-e17e-4a63-8fb9-3fe471807df9" />
)

*Two-panel layout: persona sidebar (left) + live re-ranked results with score breakdown (right)*

---

## Demo Videos

### Video  — Full Search Re-Ranking Walkthrough



https://github.com/user-attachments/assets/4b74fa21-a8ff-44d7-9143-03cf95e531d8



*Demonstrates persona switching, intent detection, and how the same query returns different results for Student vs Researcher*

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                      React Frontend                           │
│   Persona Selector → Query Input → Intent Badge → Score Cards │
└──────────────────────────┬───────────────────────────────────┘
                           │  POST /api/search
┌──────────────────────────▼───────────────────────────────────┐
│                    Flask Backend  (app.py)                    │
│                                                              │
│  fetcher.py                  ranker.py                       │
│  ┌─────────────────┐   ┌────────────────────────────────┐   │
│  │  DuckDuckGo     │   │     8-Feature ML Pipeline       │   │
│  │  HTML scraper   │──▶│  F1: TF-IDF        (lexical)   │   │
│  │                 │   │  F2: Sentence-BERT  (semantic)  │   │
│  │  + 7 query-aware│   │  F3: Freshness      (temporal)  │   │
│  │  demo corpora   │   │  F4: Title Match    (lexical)   │   │
│  └─────────────────┘   │  F5: Snippet Depth  (content)  │   │
│                        │  F6: Keyword Density (lexical)  │   │
│                        │  F7: Persona Match   (semantic) │   │
│                        │  F8: Domain Boost    (additive) │   │
│                        └───────────────┬────────────────┘   │
│                    Intent Detection    │                      │
│                    (tool/learn/fix/    │  Weighted composite  │
│                    research/news/      │  score → re-ranked   │
│                    compare/general)    ▼  results JSON        │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **8-feature scoring pipeline** | Combines lexical (TF-IDF, title match, keyword density), semantic (Sentence-BERT, persona match), temporal (freshness), content (snippet depth), and domain boost signals |
| **Query intent detection** | Detects 6 intents — tool search, learn, fix/debug, research, news, compare — and adjusts feature weights accordingly |
| **8 persona profiles** | Student, Researcher, Developer, Journalist, Business, Casual, Medical, Legal — each with custom feature weights |
| **Query-aware demo corpus** | 7 topic corpora (AI music, AI image, AI video, AI writing, coding, medical, research…) so demo results are always relevant to the query |
| **Live search** | DuckDuckGo HTML scraping — no API key required |
| **Relative score bars** | Top result = full bar; all others shown relative to it — no confusing raw percentages |
| **Persona comparison** | `/api/compare` re-ranks the same query across all 8 personas simultaneously |

---

## Project Structure

```
contex re-rank/
├── app.py             # Flask API server
├── ranker.py          # 8-feature re-ranking engine + 8 persona profiles + intent detection
├── fetcher.py         # DuckDuckGo scraper + 7 query-aware demo corpora
├── requirements.txt   # Python dependencies
├── assets/            # Demo screenshots and videos (for README)
└── frontend/
    ├── src/
    │   ├── App.jsx    # Main React UI (two-panel layout)
    │   ├── App.css    # Full CSS design system
    │   └── index.css  # Reset + root styles
    ├── package.json
    └── vite.config.js
```

---

## Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start Flask server
# (Sentence-BERT model downloads on first run — takes ~30s)
python app.py
# → Running on http://localhost:5050
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → Running on http://localhost:5173
```

Open `http://localhost:5173` in your browser. The backend must be running for live search; toggle **Demo** in the sidebar to use the built-in corpus without a network call.

---

## API Reference

### `POST /api/search`
Re-rank results for a query under a chosen persona.

```json
{
  "query": "AI tools for music generation",
  "persona": "Student",
  "use_demo": true
}
```

**Response includes:**
- `results` — re-ranked list with `composite_score`, `rank_delta`, `features` (8 values), and `intent`
- `meta.intent` — detected query intent
- `meta.weights` — effective feature weights used
- `meta.moved_up` / `moved_down` — how many results shifted position

### `GET /api/personas`
Returns all 8 persona profiles with weights and intent configurations.

### `POST /api/compare`
Re-ranks the same query across all 8 personas, returns top-3 per persona for side-by-side comparison.

---

## 8-Feature Scoring Pipeline

| # | Feature | Type | Description |
|---|---------|------|-------------|
| F1 | TF-IDF Similarity | Lexical | Bigram TF-IDF cosine similarity between query and snippet |
| F2 | Semantic Similarity | Semantic | Sentence-BERT (`all-MiniLM-L6-v2`) cosine similarity |
| F3 | Freshness | Temporal | Recency signals — year mentions, "latest", "2025" etc. |
| F4 | Title Match | Lexical | Query token overlap in result title |
| F5 | Snippet Depth | Content | Snippet length + vocabulary diversity (type-token ratio) |
| F6 | Keyword Density | Lexical | Query term density within snippet |
| F7 | Persona Match | Semantic | SBERT cosine between persona profile text and snippet |
| F8 | Domain Boost | Additive | +0.10 flat bonus for results from persona-preferred domains |

Composite score = weighted sum of F1–F7 + additive F8.
Weights are normalised to sum to 1 and shift per detected intent.

---

## 8 Persona Profiles

| Persona | Icon | Focus | Top Feature Weight |
|---------|------|-------|-------------------|
| Student | 🎓 | Tutorials & learning | Semantic 0.35 |
| Researcher | 🔬 | Papers & citations | Semantic 0.40 |
| Developer | 💻 | Code & docs | TF-IDF 0.35 |
| Journalist | 📰 | News & facts | Freshness 0.25 |
| Business | 📊 | Strategy & markets | Balanced |
| Casual | 🌐 | General browsing | Title Match 0.18 |
| Medical | 🩺 | Healthcare | Semantic 0.38 |
| Legal | ⚖️ | Laws & regulations | Semantic 0.32 |

---

## Query Intent Detection

The engine detects intent from the query and adjusts feature weights before scoring:

| Intent | Trigger Example | Weight Adjustment |
|--------|----------------|-------------------|
| **tool** | "best AI tools for…" | Boosts TF-IDF + title match |
| **learn** | "how to learn Python" | Boosts semantic + snippet depth |
| **fix** | "Python import error fix" | Boosts TF-IDF + keyword density |
| **research** | "NLP survey paper 2025" | Boosts semantic + freshness |
| **news** | "latest GPT-4 update" | Boosts freshness |
| **compare** | "React vs Vue 2025" | Balanced weights |

---

## Results

- Re-ranking shifts 5–7 of 10 results from their original position per persona
- Query intent detection routes to the correct topic corpus, eliminating irrelevant results (e.g. music queries no longer return image generation tools)
- Zero cost to run — no API keys, no model training, no cloud dependencies

---

## Tech Stack Details

| Component | Technology | Why |
|-----------|-----------|-----|
| Semantic scoring | `sentence-transformers` (`all-MiniLM-L6-v2`) | Fast, high-quality embeddings; runs on CPU |
| Lexical scoring | `scikit-learn` TfidfVectorizer (bigrams) | Captures phrase-level query matches |
| Web search | DuckDuckGo HTML scraping | No API key required |
| Backend | Flask + flask-cors | Lightweight, easy to run locally |
| Frontend | React + Vite | Fast HMR, minimal boilerplate |

---

*Built as a portfolio project demonstrating NLP re-ranking, persona-aware search personalisation, and full-stack ML integration.*
