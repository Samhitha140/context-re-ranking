"""
ContextRank Flask API Server
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__)) 

from ranker import rerank, get_persona_info, list_personas, PERSONA_DEFINITIONS
from fetcher import fetch_results, get_demo_results 
app = Flask(__name__)
CORS(app)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "name": "ContextRank API",
        "status": "ok",
        "endpoints": {
            "GET  /api/health": "Health check",
            "GET  /api/personas": "List all personas",
            "POST /api/search": "Search + re-rank  { query, persona, use_demo }",
            "POST /api/compare": "Compare all personas { query, use_demo }",
        }
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "ContextRank API running"})


@app.route('/api/personas', methods=['GET'])
def personas():
    """Return all persona profiles"""
    result = {}
    for name in list_personas():
        result[name] = get_persona_info(name)
    return jsonify(result)


@app.route('/api/search', methods=['POST'])
def search():
    """
    Main search + re-rank endpoint.
    Body: { query: str, persona: str, use_demo: bool }
    """
    data = request.get_json(silent=True) or {}
    query   = data.get('query', '').strip()
    persona = data.get('persona', 'Casual')
    use_demo = data.get('use_demo', False)

    if not query:
        return jsonify({"error": "query is required"}), 400

    t0 = time.time()

    # 1. Fetch raw results
    if use_demo:
        raw_results = get_demo_results(query, 10)
    else:
        raw_results = fetch_results(query, 10)

    fetch_time = round((time.time() - t0) * 1000)

    # 2. Re-rank
    t1 = time.time()
    ranked = rerank(query, raw_results, persona)
    rank_time = round((time.time() - t1) * 1000)

    # 3. Build analytics
    moved_up   = sum(1 for r in ranked if r['rank_delta'] > 0)
    moved_down = sum(1 for r in ranked if r['rank_delta'] < 0)
    avg_score  = round(sum(r['composite_score'] for r in ranked) / max(len(ranked), 1), 4)

    weights = PERSONA_DEFINITIONS.get(persona, {}).get('weights', {})

    return jsonify({
        "query": query,
        "persona": persona,
        "results": ranked,
        "meta": {
            "total": len(ranked),
            "fetch_ms": fetch_time,
            "rank_ms": rank_time,
            "total_ms": fetch_time + rank_time,
            "avg_composite_score": avg_score,
            "moved_up": moved_up,
            "moved_down": moved_down,
            "weights": weights,
        }
    })


@app.route('/api/compare', methods=['POST'])
def compare():
    """
    Compare re-ranking across ALL personas for the same query.
    Body: { query: str, use_demo: bool }
    Returns top-3 results per persona.
    """
    data = request.get_json(silent=True) or {}
    query    = data.get('query', '').strip()
    use_demo = data.get('use_demo', False)

    if not query:
        return jsonify({"error": "query is required"}), 400

    if use_demo:
        raw = get_demo_results(query, 10)
    else:
        raw = fetch_results(query, 10)

    comparison = {}
    for persona in list_personas():
        ranked = rerank(query, list(raw), persona)
        comparison[persona] = {
            "top3": ranked[:3],
            "avg_score": round(sum(r['composite_score'] for r in ranked) / max(len(ranked), 1), 4),
        }

    return jsonify({"query": query, "raw_count": len(raw), "comparison": comparison})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ContextRank API starting on http://localhost:5050")
    print("="*60 + "\n")
    app.run(port=5050, debug=False)