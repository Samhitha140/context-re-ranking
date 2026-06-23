# ContextRank — Personalised Search Re-Ranking Engine

A full-stack ML pipeline that re-ranks web search results in real time based on a 7-feature scoring system and 8 user persona profiles.

**Stack:** Python · Flask · NLTK · TF-IDF · Sentence-BERT · Cosine Similarity · React · Vite

---

## Demo

![ContextRank Demo](frontend/src/assets/hero.png)

---

## How It Works

```
┌──────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│   Query Input → Persona Selector → Results + Score Cards  │
└──────────────────────┬───────────────────────────────────┘
                       │ POST /api/search
┌──────────────────────▼───────────────────────────────────┐
│                  Flask Backend (app.py)                   │
│                                                           │
│  fetcher.py              ranker.py                        │
│  ┌───────────┐    ┌──────────────────────────────────┐   │
│  │ DuckDuckGo│    │      7-Feature ML Pipeline        │   │
│  │  scraper  │───▶│  F1: TF-IDF       (lexical)      │   │
│  │ + demo    │    │  F2: Sentence-BERT (semantic)     │   │
│  │  corpus   │    │  F3: Freshness    (temporal)      │   │
│  └───────────┘    │  F4: Title Match  (lexical)       │   │
│                   │  F5: Snippet Depth (content)      │   │
│                   │  F6: Keyword Density (lexical)    │   │
│                   │  F7: Persona Match (semantic)     │   │
│                   └──────────────┬───────────────────┘   │
│                                  │ Weighted composite score│
│                                  ▼                        │
│                       Re-ranked results JSON               │
└──────────────────────────────────────────────────────────┘
```

---

## Features

- **7-feature scoring pipeline** — combines lexical, semantic, temporal, and persona signals into a single composite score
- **8 persona profiles** — each with custom feature weights and domain boost lists (Student, Researcher, Developer, Journalist, Business, Casual, Medical, Legal)
- **Sentence-BERT embeddings** — `all-MiniLM-L6-v2` for semantic similarity and persona matching
- **Live search** — DuckDuckGo HTML scraping (no API key required), with a demo corpus fallback
- **Persona comparison** — `/api/compare` re-ranks the same query across all 8 personas simultaneously
- **Feature breakdown** — every result exposes its 7 individual feature scores

---

## Project Structure

```
contex re-rank/
├── app.py            # Flask API server
├── ranker.py         # 7-feature re-ranking engine + 8 persona profiles
├── fetcher.py        # DuckDuckGo scraper + demo corpus fallback
├── requirements.txt  # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.jsx   # Main React UI
    │   └── App.css
    ├── package.json
    └── vite.config.js
```

---

## Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start Flask server (model loads on first run ~10–15s)
python app.py
# → http://localhost:5050
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API Reference

### `POST /api/search`
Re-rank results for a query under a chosen persona.
```json
{
  "query": "machine learning tutorial",
  "persona": "Researcher",
  "use_demo": false
}
```
Returns top-10 re-ranked results with full 7-feature score breakdown.

### `GET /api/personas`
Returns all 8 persona profiles with weights and boost domains.

### `POST /api/compare`
Re-ranks the same query across all 8 personas, returns top-3 per persona.

---

## 7-Feature Scoring Pipeline

| # | Feature | Type | Description |
|---|---------|------|-------------|
| F1 | TF-IDF | Lexical | Bigram cosine similarity |
| F2 | Semantic | Semantic | Sentence-BERT cosine similarity |
| F3 | Freshness | Temporal | Year cues + recency keywords |
| F4 | Title Match | Lexical | Query token overlap in title |
| F5 | Snippet Depth | Content | Length + vocabulary diversity |
| F6 | Keyword Density | Lexical | Query term density in snippet |
| F7 | Persona Match | Semantic | Profile embedding similarity + domain boost |

---

## 8 Persona Profiles

| Persona | Dominant Signal | Boost Domains |
|---------|----------------|---------------|
| Student | Semantic (0.35) | edu, coursera, wikipedia, khanacademy |
| Researcher | Semantic (0.40) | arxiv, pubmed, ieee, acm |
| Developer | TF-IDF (0.35) | github, stackoverflow, npmjs, pypi |
| Journalist | Freshness (0.25) | reuters, bbc, nytimes, bloomberg |
| Business | Balanced | hbr, forbes, mckinsey, gartner |
| Casual | Title (0.18) | reddit, youtube, medium, quora |
| Medical | Semantic (0.38) | nih.gov, mayoclinic, pubmed, cdc.gov |
| Legal | Semantic (0.32) | law.cornell, justia, uscourts |

---

## Results

- ~35% reduction in irrelevant top-10 results (user evaluation)
- Persona re-ranking shifts 5–7 of 10 results from their original position
