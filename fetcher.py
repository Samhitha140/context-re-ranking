"""
Search Result Fetcher — uses DuckDuckGo HTML scraping (no API key required)
Falls back to mock results if network is unavailable.
"""

import requests
import re
import time
from urllib.parse import quote_plus, urlparse
import random


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MOCK_CORPUS = {
    "default": [
        {
            "title": "Introduction to Machine Learning — A Comprehensive Guide",
            "url": "https://www.coursera.org/learn/machine-learning",
            "snippet": "Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience. This comprehensive course covers supervised and unsupervised learning, neural networks, and practical applications.",
        },
        {
            "title": "Deep Learning with Python — Official TensorFlow Documentation",
            "url": "https://www.tensorflow.org/tutorials/keras/classification",
            "snippet": "TensorFlow and Keras make it easy to build and train deep learning models. This tutorial demonstrates training a neural network model to classify images of clothing using the Fashion MNIST dataset.",
        },
        {
            "title": "arXiv:2106.01234 — Attention Is All You Need: Transformer Architecture",
            "url": "https://arxiv.org/abs/2106.01234",
            "snippet": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable.",
        },
        {
            "title": "Stack Overflow — How to implement cosine similarity in Python",
            "url": "https://stackoverflow.com/questions/1746501/cosine-similarity",
            "snippet": "from sklearn.metrics.pairwise import cosine_similarity import numpy as np. This function computes the cosine similarity between two vectors. Here's a working implementation with detailed explanation and performance tips.",
        },
        {
            "title": "GitHub — sentence-transformers/sentence-transformers",
            "url": "https://github.com/UKPLab/sentence-transformers",
            "snippet": "Sentence-Transformers is a Python framework for state-of-the-art sentence, text and image embeddings. The initial work is described in the paper: Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.",
        },
        {
            "title": "Wikipedia — Natural Language Processing Overview",
            "url": "https://en.wikipedia.org/wiki/Natural_language_processing",
            "snippet": "Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data.",
        },
        {
            "title": "MIT OpenCourseWare — Introduction to Algorithms",
            "url": "https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms",
            "snippet": "This course provides an introduction to mathematical modeling of computational problems. It covers the common algorithms, algorithmic paradigms, and data structures used to solve these problems. Lecture notes, problem sets, and exams are provided.",
        },
        {
            "title": "Nature — Latest Research in Artificial Intelligence 2024",
            "url": "https://www.nature.com/subjects/artificial-intelligence",
            "snippet": "Nature publishes peer-reviewed research on artificial intelligence, machine learning, and data science. Recent articles cover large language models, reinforcement learning, and AI safety. Published 2024.",
        },
        {
            "title": "Towards Data Science — TF-IDF Explained Simply",
            "url": "https://towardsdatascience.com/tf-idf-explained",
            "snippet": "TF-IDF stands for Term Frequency-Inverse Document Frequency. It is a numerical statistic that reflects how important a word is to a document in a corpus. This blog post explains the math and Python implementation step by step.",
        },
        {
            "title": "Reddit r/MachineLearning — Best resources for learning NLP in 2025",
            "url": "https://www.reddit.com/r/MachineLearning/comments/nlp_resources",
            "snippet": "Community-curated list of the best NLP resources for 2025. Includes free courses, books, papers, and project ideas. Updated recently with new Hugging Face tutorials and LLM fine-tuning guides.",
        },
    ]
}


def _parse_ddg_results(html: str, max_results: int = 10) -> list[dict]:
    """Parse DuckDuckGo HTML search results"""
    results = []

    # Pattern to extract result blocks
    blocks = re.findall(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]+class="[^"]*result__url[^"]*"[^>]*>(.*?)</a>.*?'
        r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
        html, re.DOTALL
    )

    for block in blocks[:max_results]:
        url, title, _, snippet = block
        title = re.sub(r'<[^>]+>', '', title).strip()
        snippet = re.sub(r'<[^>]+>', '', snippet).strip()
        url = url.strip()

        if title and url and not url.startswith('//'):
            results.append({"title": title, "url": url, "snippet": snippet})

    return results


def fetch_results(query: str, max_results: int = 10) -> list[dict]:
    """
    Fetch search results for a query via DuckDuckGo (no API key).
    Falls back to demo corpus on failure.
    """
    try:
        encoded = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}&kl=en-us"

        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()

        results = _parse_ddg_results(resp.text, max_results)
        if results:
            return results

    except Exception as e:
        print(f"[Fetcher] DDG failed ({e}), using demo corpus.")

    # Fallback: use mock corpus, make it query-relevant by injecting query terms
    base = MOCK_CORPUS["default"][:max_results]
    enriched = []
    for i, r in enumerate(base):
        r = dict(r)
        if i < 3:
            r["snippet"] = f"Regarding '{query}': " + r["snippet"]
        enriched.append(r)
    return enriched


def get_demo_results(query: str, n: int = 10) -> list[dict]:
    """Return shuffled demo results for UI testing"""
    results = list(MOCK_CORPUS["default"])
    random.shuffle(results)
    return results[:n]