"""
ContextRank Core Re-Ranking Engine
Query-aware 7-feature ML pipeline + intent detection + adaptive domain boosts.

Flow:
  1. detect_query_intent()  — classify what the user is actually looking for
  2. _apply_intent_weights() — shift persona weights toward the right signals
  3. compute_domain_boost()  — boost sources that suit this persona × intent pair
  4. Weighted composite score → re-ranked results
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

for pkg in ('punkt', 'stopwords', 'wordnet', 'punkt_tab'):
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass

STOP_WORDS = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()


# ── 8 Persona Profiles ────────────────────────────────────────────────────────
PERSONA_DEFINITIONS = {
    "Student": {
        "description": "undergraduate graduate student tutorial learn explain beginner course study understand example basics introduction lecture homework assignment definition concept simple guide step overview",
        "weights": {"tfidf": 0.30, "semantic": 0.35, "freshness": 0.05, "title": 0.15, "snippet_depth": 0.10, "keyword_density": 0.03, "persona_match": 0.02},
        "display": {"icon": "🎓", "color": "#4F7FFF", "bg": "#EEF2FF", "desc": "Tutorials & explanations"},
    },
    "Researcher": {
        "description": "academic researcher paper study research analysis journal peer-reviewed citation findings methodology hypothesis experiment data abstract conference arxiv doi published literature review survey",
        "weights": {"tfidf": 0.20, "semantic": 0.40, "freshness": 0.10, "title": 0.10, "snippet_depth": 0.12, "keyword_density": 0.04, "persona_match": 0.04},
        "display": {"icon": "🔬", "color": "#7C3AED", "bg": "#F5F3FF", "desc": "Papers & citations"},
    },
    "Developer": {
        "description": "software developer code api library framework implementation github npm documentation function class method install debug error syntax example snippet repository open-source programming",
        "weights": {"tfidf": 0.35, "semantic": 0.25, "freshness": 0.08, "title": 0.12, "snippet_depth": 0.10, "keyword_density": 0.06, "persona_match": 0.04},
        "display": {"icon": "💻", "color": "#059669", "bg": "#ECFDF5", "desc": "Code & documentation"},
    },
    "Journalist": {
        "description": "news reporter breaking latest official announced statement interview exclusive sources confirmed today recent coverage press release update investigation report journalist media",
        "weights": {"tfidf": 0.25, "semantic": 0.25, "freshness": 0.25, "title": 0.10, "snippet_depth": 0.08, "keyword_density": 0.04, "persona_match": 0.03},
        "display": {"icon": "📰", "color": "#D97706", "bg": "#FFFBEB", "desc": "News & facts"},
    },
    "Business": {
        "description": "market revenue strategy growth industry competitive ROI investment stakeholder enterprise B2B SaaS metrics forecast analysis trend quarter profit startup venture capital",
        "weights": {"tfidf": 0.28, "semantic": 0.28, "freshness": 0.15, "title": 0.12, "snippet_depth": 0.10, "keyword_density": 0.04, "persona_match": 0.03},
        "display": {"icon": "📊", "color": "#DC2626", "bg": "#FEF2F2", "desc": "Strategy & market insights"},
    },
    "Casual": {
        "description": "how what best top list review tips easy quick popular trending fun interesting watch try everyday general simple information",
        "weights": {"tfidf": 0.30, "semantic": 0.25, "freshness": 0.12, "title": 0.18, "snippet_depth": 0.08, "keyword_density": 0.04, "persona_match": 0.03},
        "display": {"icon": "🌐", "color": "#6B7280", "bg": "#F9FAFB", "desc": "General browsing"},
    },
    "Medical": {
        "description": "symptoms treatment diagnosis clinical patient therapy medication disease syndrome healthcare physician evidence clinical trial dosage side effects medical health nurse hospital",
        "weights": {"tfidf": 0.22, "semantic": 0.38, "freshness": 0.12, "title": 0.10, "snippet_depth": 0.12, "keyword_density": 0.03, "persona_match": 0.03},
        "display": {"icon": "⚕️", "color": "#0891B2", "bg": "#ECFEFF", "desc": "Healthcare information"},
    },
    "Legal": {
        "description": "law statute regulation court ruling precedent legal rights liability contract compliance jurisdiction case act section plaintiff defendant clause attorney lawyer legislation",
        "weights": {"tfidf": 0.30, "semantic": 0.32, "freshness": 0.08, "title": 0.12, "snippet_depth": 0.12, "keyword_density": 0.03, "persona_match": 0.03},
        "display": {"icon": "⚖️", "color": "#92400E", "bg": "#FEF3C7", "desc": "Laws & regulations"},
    },
}


# ── Query Intent Detection ─────────────────────────────────────────────────────
# 6 intents + "general" fallback. Phrases score 2×, words score 1×.
INTENT_KEYWORDS = {
    "tool": {
        "words": {
            "tool", "tools", "app", "apps", "software", "platform", "free", "best", "top",
            "alternative", "alternatives", "list", "website", "sites", "service", "services",
            "resource", "resources", "extension", "plugin", "library", "framework", "api",
            "product", "products", "generator", "automation", "suite", "saas", "open-source",
        },
        "phrases": [
            "free ai", "best ai", "top ai", "ai tools", "free tools", "no cost",
            "open source", "top 10", "best free", "must have", "recommended tools",
            "tool for", "apps for", "software for",
        ],
    },
    "learn": {
        "words": {
            "tutorial", "learn", "explain", "explained", "introduction", "beginner",
            "basics", "overview", "guide", "course", "lesson", "understand", "definition",
            "meaning", "example", "examples", "simple", "easy", "teach", "lecture",
            "study", "training", "concepts", "fundamentals",
        },
        "phrases": [
            "how does", "what is", "what are", "how to", "for beginners",
            "getting started", "step by step", "learn how", "beginner guide",
            "crash course", "from scratch", "101",
        ],
    },
    "fix": {
        "words": {
            "error", "fix", "debug", "issue", "problem", "solve", "solution",
            "broken", "failed", "crash", "exception", "bug", "wrong", "incorrect",
            "not", "cannot", "cant", "doesnt", "failing", "troubleshoot", "resolve",
        },
        "phrases": [
            "not working", "doesn't work", "how to fix", "resolve error",
            "stack trace", "error message", "runtime error", "not found",
            "permission denied", "keeps crashing",
        ],
    },
    "research": {
        "words": {
            "research", "paper", "papers", "study", "survey", "analysis", "arxiv",
            "journal", "academic", "publication", "findings", "methodology",
            "experiment", "literature", "review", "citation", "dataset", "benchmark",
            "empirical", "theoretical",
        },
        "phrases": [
            "research paper", "systematic review", "meta analysis", "peer reviewed",
            "state of the art", "literature review", "empirical study", "published in",
        ],
    },
    "news": {
        "words": {
            "news", "latest", "update", "updates", "announcement", "breaking",
            "recent", "today", "new", "2025", "2026", "released", "launched",
            "announced", "upcoming", "just", "this week", "current",
        },
        "phrases": [
            "latest news", "recent update", "just released", "breaking news",
            "new release", "this year", "just announced", "what happened",
        ],
    },
    "compare": {
        "words": {
            "vs", "versus", "compare", "comparison", "difference", "differences",
            "better", "which", "ranking", "review", "reviews", "pros", "cons",
            "worth", "recommend", "pick", "choose", "between",
        },
        "phrases": [
            " vs ", " versus ", "compared to", "difference between",
            "better than", "pros and cons", "side by side", "which is better",
            "should i use",
        ],
    },
}

# Intent priority when scores tie (most specific wins)
_INTENT_PRIORITY = ["fix", "tool", "research", "news", "compare", "learn"]


def detect_query_intent(query: str) -> str:
    q = query.lower()
    words = set(q.split())
    scores = {}

    for intent, signals in INTENT_KEYWORDS.items():
        score = len(words & signals["words"])
        score += sum(2 for p in signals["phrases"] if p in q)
        scores[intent] = score

    best = max(scores.values())
    if best == 0:
        return "general"

    for intent in _INTENT_PRIORITY:
        if scores[intent] == best:
            return intent

    return "general"


# ── Intent-Aware Feature Weight Overrides ─────────────────────────────────────
# Deltas applied to base persona weights; result is re-normalised to sum=1.
INTENT_WEIGHT_OVERRIDES = {
    "tool":     {"tfidf": +0.06, "title": +0.04, "freshness": -0.03, "semantic": -0.04},
    "learn":    {"semantic": +0.06, "snippet_depth": +0.03, "tfidf": -0.05, "freshness": -0.02},
    "fix":      {"tfidf": +0.08, "title": +0.04, "keyword_density": +0.03, "freshness": -0.07, "semantic": -0.05},
    "research": {"semantic": +0.09, "snippet_depth": +0.05, "freshness": +0.02, "tfidf": -0.08, "title": -0.04},
    "news":     {"freshness": +0.14, "title": +0.03, "semantic": -0.09, "snippet_depth": -0.04},
    "compare":  {"snippet_depth": +0.06, "title": +0.03, "semantic": +0.02, "freshness": -0.06},
    "general":  {},
}


def _apply_intent_weights(base: dict, intent: str) -> dict:
    overrides = INTENT_WEIGHT_OVERRIDES.get(intent, {})
    adjusted = {k: max(0.01, v + overrides.get(k, 0.0)) for k, v in base.items()}
    total = sum(adjusted.values())
    return {k: round(v / total, 4) for k, v in adjusted.items()}


# ── Intent × Persona Domain Boosts ───────────────────────────────────────────
# Each (persona, intent) pair names the domains that should rank higher.
# Applied as a direct +0.10 additive bonus to the composite score.
PERSONA_INTENT_DOMAINS = {
    "Student": {
        "tool":     ["github", "producthunt", "futurepedia", "alternativeto", "freecodecamp", "g2", "toolify"],
        "learn":    ["edu", "wikipedia", "khanacademy", "coursera", "udemy", "mit", "ocw", "freecodecamp", "geeksforgeeks", "w3schools"],
        "fix":      ["stackoverflow", "github", "geeksforgeeks", "reddit", "w3schools", "freecodecamp"],
        "research": ["wikipedia", "scholar", "medium", "towardsdatascience", "arxiv"],
        "news":     ["hackernews", "techcrunch", "theverge", "reddit"],
        "compare":  ["reddit", "alternativeto", "quora", "producthunt", "g2"],
        "general":  ["edu", "wikipedia", "khanacademy", "coursera"],
    },
    "Researcher": {
        "tool":     ["github", "paperswithcode", "huggingface", "arxiv", "kaggle", "colab"],
        "learn":    ["arxiv", "scholar", "wikipedia", "ieee", "acm", "mit", "springer"],
        "fix":      ["stackoverflow", "github", "arxiv", "docs", "superuser"],
        "research": ["arxiv", "scholar", "pubmed", "ieee", "acm", "nature", "science", "researchgate", "ncbi", "springer"],
        "news":     ["arxiv", "nature", "science", "ieee", "techcrunch", "wired"],
        "compare":  ["arxiv", "paperswithcode", "scholar", "wikipedia", "benchmarks"],
        "general":  ["arxiv", "scholar", "pubmed", "ieee"],
    },
    "Developer": {
        "tool":     ["github", "npmjs", "pypi", "producthunt", "devhunt", "alternativeto", "toolify"],
        "learn":    ["docs", "mdn", "dev.to", "freecodecamp", "github", "stackoverflow", "digitalocean", "css-tricks"],
        "fix":      ["stackoverflow", "github", "docs", "reddit", "superuser", "askubuntu"],
        "research": ["arxiv", "paperswithcode", "github", "hackernews", "acm"],
        "news":     ["hackernews", "techcrunch", "github", "dev.to", "theverge", "wired"],
        "compare":  ["stackoverflow", "reddit", "github", "npmjs", "alternativeto"],
        "general":  ["github", "stackoverflow", "docs"],
    },
    "Journalist": {
        "tool":     ["producthunt", "techcrunch", "wired", "alternativeto"],
        "learn":    ["wikipedia", "medium", "bbc", "reuters", "ap"],
        "fix":      ["reddit", "medium", "quora"],
        "research": ["reuters", "ap", "bbc", "guardian", "nytimes", "politifact", "factcheck"],
        "news":     ["reuters", "bbc", "guardian", "ap", "bloomberg", "cnn", "nytimes", "wsj", "ft", "aljazeera"],
        "compare":  ["reuters", "bbc", "theguardian", "politifact", "factcheck", "snopes"],
        "general":  ["reuters", "bbc", "bloomberg"],
    },
    "Business": {
        "tool":     ["producthunt", "g2", "capterra", "gartner", "getapp", "softwareadvice", "trustradius"],
        "learn":    ["hbr", "coursera", "linkedin", "mckinsey", "mit", "harvard"],
        "fix":      ["hbr", "reddit", "stackoverflow", "quora", "medium"],
        "research": ["mckinsey", "gartner", "hbr", "bloomberg", "statista", "forrester", "deloitte"],
        "news":     ["bloomberg", "wsj", "ft", "techcrunch", "forbes", "businessinsider", "fortune"],
        "compare":  ["g2", "capterra", "gartner", "hbr", "forrester", "trustradius"],
        "general":  ["hbr", "forbes", "mckinsey"],
    },
    "Casual": {
        "tool":     ["producthunt", "reddit", "youtube", "alternativeto", "lifehacker", "toolify"],
        "learn":    ["youtube", "reddit", "wikipedia", "medium", "quora", "wikihow"],
        "fix":      ["reddit", "youtube", "wikihow", "stackoverflow", "quora"],
        "research": ["wikipedia", "reddit", "medium", "youtube", "quora"],
        "news":     ["reddit", "cnn", "bbc", "youtube", "buzzfeed", "theverge"],
        "compare":  ["reddit", "youtube", "wirecutter", "quora", "rtings"],
        "general":  ["reddit", "youtube", "medium", "wikipedia"],
    },
    "Medical": {
        "tool":     ["nih.gov", "cdc.gov", "who.int", "healthline", "medscape", "epocrates"],
        "learn":    ["mayoclinic", "webmd", "medlineplus", "nih.gov", "healthline", "clevelandclinic"],
        "fix":      ["mayoclinic", "webmd", "nih.gov", "healthline", "reddit", "drugs.com"],
        "research": ["pubmed", "nih.gov", "who.int", "ncbi", "nature", "medscape", "nejm", "thelancet"],
        "news":     ["nih.gov", "who.int", "nature", "medscape", "healthline", "statnews", "medpagetoday"],
        "compare":  ["mayoclinic", "webmd", "pubmed", "healthline", "drugs.com"],
        "general":  ["nih.gov", "mayoclinic", "pubmed", "medlineplus"],
    },
    "Legal": {
        "tool":     ["findlaw", "legalzoom", "westlaw", "lexisnexis", "nolo", "avvo", "rocketlawyer"],
        "learn":    ["law.cornell", "findlaw", "justia", "nolo", "wikipedia", "oyez"],
        "fix":      ["findlaw", "justia", "nolo", "avvo", "reddit", "quora"],
        "research": ["law.cornell", "justia", "uscourts", "scholar", "findlaw", "oyez", "courtlistener"],
        "news":     ["scotusblog", "law.com", "findlaw", "reuters", "bloomberg", "abajournal"],
        "compare":  ["findlaw", "justia", "nolo", "avvo", "martindale"],
        "general":  ["law.cornell", "justia", "findlaw", "nolo"],
    },
}

DOMAIN_BOOST_VALUE = 0.10   # additive bonus on composite score for matched domains


# ── Model Init ────────────────────────────────────────────────────────────────
print("[ContextRank] Initialising Sentence-BERT model (all-MiniLM-L6-v2)…")
SBERT_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

print("[ContextRank] Computing persona embeddings…")
PERSONA_EMBEDDINGS = {}
for _name, _profile in PERSONA_DEFINITIONS.items():
    PERSONA_EMBEDDINGS[_name] = SBERT_MODEL.encode([_profile["description"]])[0]
print("[ContextRank] Engine ready ✓")


# ── Text Utilities ─────────────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return ' '.join(tokens)


# ── 7 Feature Scoring Functions ────────────────────────────────────────────────
def compute_tfidf_score(query: str, docs: list) -> np.ndarray:
    corpus = [preprocess(query)] + [preprocess(d) for d in docs]
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True)
    mat = vec.fit_transform(corpus)
    return cosine_similarity(mat[0:1], mat[1:]).flatten()


def compute_semantic_score(query: str, docs: list) -> np.ndarray:
    embeddings = SBERT_MODEL.encode([query] + docs)
    scores = cosine_similarity(embeddings[0:1], embeddings[1:]).flatten()
    return np.clip(scores, 0, 1)


def compute_freshness_score(results: list) -> np.ndarray:
    year_re = re.compile(r'\b(202[0-9]|201[5-9])\b')
    fresh_words = {'today', 'latest', 'recent', 'new', '2024', '2025', '2026',
                   'updated', 'breaking', 'just', 'announced', 'released'}
    scores = []
    for r in results:
        text = (r.get('title', '') + ' ' + r.get('snippet', '') + ' ' + r.get('url', '')).lower()
        score = 0.45
        years = year_re.findall(text)
        if years:
            score = 0.3 + min((max(int(y) for y in years) - 2015) / 11, 1.0) * 0.7
        if any(w in text for w in fresh_words):
            score = min(score + 0.15, 1.0)
        scores.append(score)
    return np.array(scores)


def compute_title_match_score(query: str, results: list) -> np.ndarray:
    q_tokens = set(preprocess(query).split())
    scores = []
    for r in results:
        t = set(preprocess(r.get('title', '')).split())
        scores.append(min(len(q_tokens & t) / max(len(q_tokens), 1), 1.0) if t and q_tokens else 0.0)
    return np.array(scores)


def compute_snippet_depth_score(results: list) -> np.ndarray:
    scores = []
    for r in results:
        s = r.get('snippet', '')
        words = s.split()
        length_score = min(len(s) / 300, 1.0)
        diversity = len(set(w.lower() for w in words)) / max(len(words), 1)
        scores.append(round(0.6 * length_score + 0.4 * diversity, 4))
    return np.array(scores)


def compute_keyword_density_score(query: str, results: list) -> np.ndarray:
    q_tokens = set(preprocess(query).split())
    scores = []
    for r in results:
        words = (r.get('title', '') + ' ' + r.get('snippet', '')).lower().split()
        if not words or not q_tokens:
            scores.append(0.0)
            continue
        scores.append(min(sum(1 for w in words if w in q_tokens) / len(words) * 10, 1.0))
    return np.array(scores)


def compute_persona_match_score(persona: str, results: list) -> np.ndarray:
    persona_emb = PERSONA_EMBEDDINGS[persona]
    doc_texts = [r.get('title', '') + ' ' + r.get('snippet', '') for r in results]
    doc_embs = SBERT_MODEL.encode(doc_texts)
    return np.clip(cosine_similarity([persona_emb], doc_embs).flatten(), 0, 1)


def compute_domain_boost(persona: str, intent: str, results: list) -> np.ndarray:
    domains = (
        PERSONA_INTENT_DOMAINS.get(persona, {}).get(intent)
        or PERSONA_INTENT_DOMAINS.get(persona, {}).get("general", [])
    )
    return np.array([
        DOMAIN_BOOST_VALUE if any(d in r.get('url', '').lower() for d in domains) else 0.0
        for r in results
    ])


# ── Main Re-Ranker ─────────────────────────────────────────────────────────────
def rerank(query: str, results: list, persona: str = "Casual") -> list:
    if not results:
        return []

    persona = persona if persona in PERSONA_DEFINITIONS else "Casual"
    intent  = detect_query_intent(query)
    weights = _apply_intent_weights(PERSONA_DEFINITIONS[persona]["weights"], intent)

    docs = [r.get('title', '') + ' ' + r.get('snippet', '') for r in results]

    f1  = compute_tfidf_score(query, docs)
    f2  = compute_semantic_score(query, docs)
    f3  = compute_freshness_score(results)
    f4  = compute_title_match_score(query, results)
    f5  = compute_snippet_depth_score(results)
    f6  = compute_keyword_density_score(query, results)
    f7  = compute_persona_match_score(persona, results)
    f8  = compute_domain_boost(persona, intent, results)

    composite = (
        weights["tfidf"]           * f1 +
        weights["semantic"]        * f2 +
        weights["freshness"]       * f3 +
        weights["title"]           * f4 +
        weights["snippet_depth"]   * f5 +
        weights["keyword_density"] * f6 +
        weights["persona_match"]   * f7 +
        f8   # domain boost is a direct additive term, not weighted down
    )

    ranked = []
    for i, r in enumerate(results):
        ranked.append({
            **r,
            "original_rank": i + 1,
            "composite_score": round(float(composite[i]), 4),
            "intent": intent,
            "features": {
                "tfidf":           round(float(f1[i]), 4),
                "semantic":        round(float(f2[i]), 4),
                "freshness":       round(float(f3[i]), 4),
                "title_match":     round(float(f4[i]), 4),
                "snippet_depth":   round(float(f5[i]), 4),
                "keyword_density": round(float(f6[i]), 4),
                "persona_match":   round(float(f7[i]), 4),
                "domain_boost":    round(float(f8[i]), 4),
            },
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
        "display": p["display"],
    }


def list_personas() -> list:
    return list(PERSONA_DEFINITIONS.keys())
