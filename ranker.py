"""
ContextRank Core Re-Ranking Engine
7-feature ML pipeline: TF-IDF (lexical) + Sentence-BERT (semantic)
+ Freshness + Title Match + Snippet Depth + Keyword Density + Persona Match
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
import math

# ── NLTK setup ──────────────────────────────────────────────────────────────
for pkg in ('punkt', 'stopwords', 'wordnet', 'punkt_tab'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass

STOP_WORDS = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# ── 8 Persona Profiles ───────────────────────────────────────────────────────
PERSONA_DEFINITIONS = {
    "Student": {
        "description": "undergraduate graduate student tutorial learn explain beginner course study understand example basics introduction lecture homework assignment definition concept simple guide step overview",
        "weights": {"tfidf": 0.30, "semantic": 0.35, "freshness": 0.05, "title": 0.15, "snippet_depth": 0.10, "keyword_density": 0.03, "persona_match": 0.02},
        "boost_domains": ["edu", "wikipedia", "khanacademy", "coursera", "udemy", "stackoverflow", "mit", "ocw"],
        "display": {"icon": "🎓", "color": "#4F7FFF", "bg": "#EEF2FF", "desc": "Tutorials & explanations"},
    },
    "Researcher": {
        "description": "academic researcher paper study research analysis journal peer-reviewed citation findings methodology hypothesis experiment data abstract conference arxiv doi published literature review survey",
        "weights": {"tfidf": 0.20, "semantic": 0.40, "freshness": 0.10, "title": 0.10, "snippet_depth": 0.12, "keyword_density": 0.04, "persona_match": 0.04},
        "boost_domains": ["arxiv", "scholar", "pubmed", "ieee", "acm", "researchgate", "ncbi", "nature", "science"],
        "display": {"icon": "🔬", "color": "#7C3AED", "bg": "#F5F3FF", "desc": "Papers & citations"},
    },
    "Developer": {
        "description": "software developer code api library framework implementation github npm documentation function class method install debug error syntax example snippet repository open-source programming",
        "weights": {"tfidf": 0.35, "semantic": 0.25, "freshness": 0.08, "title": 0.12, "snippet_depth": 0.10, "keyword_density": 0.06, "persona_match": 0.04},
        "boost_domains": ["github", "stackoverflow", "docs", "npmjs", "pypi", "developer", "dev.to", "gitlab"],
        "display": {"icon": "💻", "color": "#059669", "bg": "#ECFDF5", "desc": "Code & documentation"},
    },
    "Journalist": {
        "description": "news reporter breaking latest official announced statement interview exclusive sources confirmed today recent coverage press release update investigation report journalist media",
        "weights": {"tfidf": 0.25, "semantic": 0.25, "freshness": 0.25, "title": 0.10, "snippet_depth": 0.08, "keyword_density": 0.04, "persona_match": 0.03},
        "boost_domains": ["reuters", "bbc", "nytimes", "guardian", "ap", "bloomberg", "wsj", "cnn", "abc"],
        "display": {"icon": "📰", "color": "#D97706", "bg": "#FFFBEB", "desc": "News & facts"},
    },
    "Business": {
        "description": "market revenue strategy growth industry competitive ROI investment stakeholder enterprise B2B SaaS metrics forecast analysis trend quarter profit startup venture capital",
        "weights": {"tfidf": 0.28, "semantic": 0.28, "freshness": 0.15, "title": 0.12, "snippet_depth": 0.10, "keyword_density": 0.04, "persona_match": 0.03},
        "boost_domains": ["hbr", "forbes", "bloomberg", "mckinsey", "gartner", "techcrunch", "wsj", "ft"],
        "display": {"icon": "📊", "color": "#DC2626", "bg": "#FEF2F2", "desc": "Strategy & market insights"},
    },
    "Casual": {
        "description": "how what best top list review tips easy quick popular trending fun interesting watch try everyday general simple information",
        "weights": {"tfidf": 0.30, "semantic": 0.25, "freshness": 0.12, "title": 0.18, "snippet_depth": 0.08, "keyword_density": 0.04, "persona_match": 0.03},
        "boost_domains": ["reddit", "youtube", "medium", "quora", "wikipedia"],
        "display": {"icon": "🌐", "color": "#6B7280", "bg": "#F9FAFB", "desc": "General browsing"},
    },
    "Medical": {
        "description": "symptoms treatment diagnosis clinical patient therapy medication disease syndrome healthcare physician evidence clinical trial dosage side effects medical health nurse hospital",
        "weights": {"tfidf": 0.22, "semantic": 0.38, "freshness": 0.12, "title": 0.10, "snippet_depth": 0.12, "keyword_density": 0.03, "persona_match": 0.03},
        "boost_domains": ["nih.gov", "mayoclinic", "webmd", "pubmed", "medlineplus", "who.int", "cdc.gov", "nhs"],
        "display": {"icon": "⚕️", "color": "#0891B2", "bg": "#ECFEFF", "desc": "Healthcare information"},
    },
    "Legal": {
        "description": "law statute regulation court ruling precedent legal rights liability contract compliance jurisdiction case act section plaintiff defendant clause attorney lawyer legislation",
        "weights": {"tfidf": 0.30, "semantic": 0.32, "freshness": 0.08, "title": 0.12, "snippet_depth": 0.12, "keyword_density": 0.03, "persona_match": 0.03},
        "boost_domains": ["law.cornell", "justia", "findlaw", "uscourts", "legislation.gov", "gov"],
        "display": {"icon": "⚖️", "color": "#92400E", "bg": "#FEF3C7", "desc": "Laws & regulations"},
    },
}

print("[ContextRank] Initialising Sentence-BERT model (all-MiniLM-L6-v2)…")
SBERT_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

# Pre-compute persona embeddings
print("[ContextRank] Computing persona embeddings…")
PERSONA_EMBEDDINGS = {}
for name, profile in PERSONA_DEFINITIONS.items():
    emb = SBERT_MODEL.encode([profile["description"]])[0]
    PERSONA_EMBEDDINGS[name] = emb
print("[ContextRank] Engine ready ✓")

# ─────────────────────────────────────────────────────────────────────────────
#  Text utilities
# ─────────────────────────────────────────────────────────────────────────────

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return ' '.join(tokens)


def extract_domain(url: str) -> str:
    return url.lower()


# ─────────────────────────────────────────────────────────────────────────────
#  7-Feature Scoring Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def compute_tfidf_score(query: str, docs: list) -> np.ndarray:
    """Feature 1: TF-IDF lexical cosine similarity"""
    corpus = [preprocess(query)] + [preprocess(d) for d in docs]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    return scores


def compute_semantic_score(query: str, docs: list) -> np.ndarray:
    """Feature 2: LSA semantic similarity (Sentence-BERT proxy)"""
    all_texts = [query] + docs
    embeddings = SBERT_MODEL.encode(all_texts)
    query_emb = embeddings[0:1]
    doc_embs = embeddings[1:]
    scores = cosine_similarity(query_emb, doc_embs).flatten()
    return np.clip(scores, 0, 1)


def compute_freshness_score(results: list) -> np.ndarray:
    """Feature 3: Recency signal from text cues"""
    scores = []
    year_pattern = re.compile(r'\b(202[0-9]|201[5-9])\b')
    fresh_words = {'today', 'latest', 'recent', 'new', '2024', '2025', '2026',
                   'updated', 'breaking', 'just', 'announced', 'released'}
    for r in results:
        text = (r.get('title','') + ' ' + r.get('snippet','') + ' ' + r.get('url','')).lower()
        score = 0.45
        years = year_pattern.findall(text)
        if years:
            latest = max(int(y) for y in years)
            score = 0.3 + min((latest - 2015) / 11, 1.0) * 0.7
        for w in fresh_words:
            if w in text:
                score = min(score + 0.15, 1.0)
                break
        scores.append(score)
    return np.array(scores)


def compute_title_match_score(query: str, results: list) -> np.ndarray:
    """Feature 4: Query term overlap in title (lexical)"""
    q_tokens = set(preprocess(query).split())
    scores = []
    for r in results:
        title_tokens = set(preprocess(r.get('title', '')).split())
        if not title_tokens or not q_tokens:
            scores.append(0.0)
            continue
        overlap = len(q_tokens & title_tokens)
        score = overlap / max(len(q_tokens), 1)
        scores.append(min(score, 1.0))
    return np.array(scores)


def compute_snippet_depth_score(results: list) -> np.ndarray:
    """Feature 5: Snippet richness / informativeness"""
    scores = []
    for r in results:
        snippet = r.get('snippet', '')
        length_score = min(len(snippet) / 300, 1.0)
        words = snippet.split()
        diversity = len(set(w.lower() for w in words)) / max(len(words), 1)
        score = 0.6 * length_score + 0.4 * diversity
        scores.append(round(score, 4))
    return np.array(scores)


def compute_keyword_density_score(query: str, results: list) -> np.ndarray:
    """Feature 6: Query keyword density in snippet"""
    q_tokens = set(preprocess(query).split())
    scores = []
    for r in results:
        text = (r.get('title','') + ' ' + r.get('snippet','')).lower()
        words = text.split()
        if not words or not q_tokens:
            scores.append(0.0)
            continue
        hits = sum(1 for w in words if w in q_tokens)
        density = hits / len(words)
        scores.append(min(density * 10, 1.0))
    return np.array(scores)


def compute_persona_match_score(persona: str, query: str, results: list) -> np.ndarray:
    """Feature 7: Persona-profile semantic similarity + domain boost"""
    profile = PERSONA_DEFINITIONS.get(persona, PERSONA_DEFINITIONS["Casual"])
    persona_emb = PERSONA_EMBEDDINGS[persona]
    boost_domains = profile["boost_domains"]

    # Encode document texts
    doc_texts = [r.get('title','') + ' ' + r.get('snippet','') for r in results]
    doc_embs = SBERT_MODEL.encode(doc_texts)

    semantic_scores = cosine_similarity([persona_emb], doc_embs).flatten()

    # Domain boost
    domain_bonuses = np.array([
        0.18 if any(d in r.get('url','').lower() for d in boost_domains) else 0.0
        for r in results
    ])

    return np.clip(semantic_scores + domain_bonuses, 0, 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Main Re-Ranker
# ─────────────────────────────────────────────────────────────────────────────

def rerank(query: str, results: list, persona: str = "Casual") -> list:
    if not results:
        return []

    persona = persona if persona in PERSONA_DEFINITIONS else "Casual"
    weights = PERSONA_DEFINITIONS[persona]["weights"]

    # Build document corpus
    docs = [r.get('title','') + ' ' + r.get('snippet','') for r in results]

    # Compute all 7 features
    f1_tfidf    = compute_tfidf_score(query, docs)
    f2_semantic = compute_semantic_score(query, docs)
    f3_fresh    = compute_freshness_score(results)
    f4_title    = compute_title_match_score(query, results)
    f5_snippet  = compute_snippet_depth_score(results)
    f6_keyword  = compute_keyword_density_score(query, results)
    f7_persona  = compute_persona_match_score(persona, query, results)

    # Weighted composite score
    composite = (
        weights["tfidf"]          * f1_tfidf    +
        weights["semantic"]       * f2_semantic  +
        weights["freshness"]      * f3_fresh     +
        weights["title"]          * f4_title     +
        weights["snippet_depth"]  * f5_snippet   +
        weights["keyword_density"]* f6_keyword   +
        weights["persona_match"]  * f7_persona
    )

    ranked = []
    for i, r in enumerate(results):
        ranked.append({
            **r,
            "original_rank": i + 1,
            "composite_score": round(float(composite[i]), 4),
            "features": {
                "tfidf":           round(float(f1_tfidf[i]), 4),
                "semantic":        round(float(f2_semantic[i]), 4),
                "freshness":       round(float(f3_fresh[i]), 4),
                "title_match":     round(float(f4_title[i]), 4),
                "snippet_depth":   round(float(f5_snippet[i]), 4),
                "keyword_density": round(float(f6_keyword[i]), 4),
                "persona_match":   round(float(f7_persona[i]), 4),
            }
        })

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    for i, r in enumerate(ranked):
        r["new_rank"] = i + 1
        r["rank_delta"] = r["original_rank"] - r["new_rank"]

    return ranked


def get_persona_info(persona: str) -> dict:
    p = PERSONA_DEFINITIONS.get(persona, PERSONA_DEFINITIONS["Casual"])
    return {
        "name": persona,
        "description": p["description"],
        "weights": p["weights"],
        "boost_domains": p["boost_domains"],
        "display": p["display"],
    }


def list_personas() -> list:
    return list(PERSONA_DEFINITIONS.keys())