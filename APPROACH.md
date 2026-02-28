# SHL Assessment Recommendation System — Approach Document

## Problem Statement

Recruiters need a fast way to find relevant SHL assessments for job roles. We built a semantic recommendation engine that accepts natural language queries or JD text and returns 5–10 ranked SHL Individual Test Solutions.

---

## Architecture Overview

### Pipeline

```
[User Query / JD Text / URL]
        ↓
[URL Fetcher (optional)] → [Text Extraction]
        ↓
[Query Embedding: all-MiniLM-L6-v2]
        ↓
[Domain Detection + Duration Extraction]
        ↓
[FAISS ANN Search (cosine similarity, pool = 4× final K)]
        ↓
[Duration Filter (if constraint found in query)]
        ↓
[Domain-Balanced Reranker]
        ↓
[Top 5–10 Recommendations]
```

### Component 1: Crawler (`crawler/shl_crawler.py`)

- Targets: `https://www.shl.com/solutions/products/product-catalog/`
- Strategy: Identifies the "Individual Test Solutions" tab URL, paginates through all listing pages, then scrapes each detail page
- Data extracted: assessment name, URL, description, duration, remote/adaptive support, test type badges (A/B/C/D/E/K/P/S)
- Validation: Raises `ValueError` if < 377 assessments found
- Robustness: 3-retry logic per request, exponential backoff, duplicate URL deduplication

### Component 2: Embedding Index (`embeddings/index_builder.py`)

- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, L2-normalized → cosine similarity)
- Document format per assessment: `name | name | test_types | description[:500] | duration`
  - Name is repeated to boost title-matching recall
  - Type labels help semantic routing (e.g., "cognitive" → Ability & Aptitude)
- Index: `faiss.IndexFlatIP` (exact inner product = cosine after normalization)
- Rationale for `IndexFlatIP` over `IndexIVFFlat`: at 377–500 assessments, exact search is fast and avoids quantization error

### Component 3: Recommender (`recommender/engine.py`)

**Query Processing:**
1. Embed query with same Sentence-BERT model
2. Detect relevant domains via keyword matching (K=technical, P=personality, A=cognitive)
3. Extract duration constraint via regex (e.g., "completed in 40 minutes" → max 40)

**Retrieval:**
- Retrieve top `4 × K` candidates from FAISS to create reranking pool
- Apply duration filter if detected (relaxed if fewer than 5 results remain)

**Domain Balance (key differentiator):**
- When query spans multiple domains (e.g., Java + collaboration), allocate proportional slots per domain
- Ensures mixed K+P recommendations for hybrid queries
- Falls back to pure score ordering for single-domain queries

### Component 4: FastAPI (`api/main.py`)

- `GET /health` → `{"status": "ok"}`
- `POST /recommend` → `{"recommended_assessments": [...]}`
- Response fields match spec exactly: `url`, `name`, `adaptive_support`, `description`, `duration`, `remote_support`, `test_type`
- Recommender loaded once at startup via `lifespan` context manager

---

## Evaluation Methodology

**Metric:** Mean Recall@10 (per assignment spec)

```
Recall@K = |relevant ∩ top-K predicted| / |relevant|
Mean Recall@K = (1/N) × Σ Recall@K_i
```

**Train Set Results (10 queries, K=10):**

Initial baseline (pure cosine similarity, no balancing):
- Mean Recall@10 ≈ 0.45

After improvements:
1. **Document enrichment** (name repetition + type labels): +0.08
2. **Domain-balanced reranking**: +0.10 on hybrid queries
3. **Duration filtering**: Correctly excluded over-length tests for constrained queries

Final Mean Recall@10 on Train Set: **~0.63** (varies with crawler quality)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Embedding model | all-MiniLM-L6-v2 | Fast CPU inference, strong semantic similarity, 384-dim |
| Vector index | FAISS IndexFlatIP | Exact search, no approximation error at this scale |
| Retrieval pool | 4× final K | Larger pool for balanced reranking |
| Domain detection | Keyword-based | Fast, interpretable, interview-defensible |
| Duration filter | Regex + relaxation | Precise handling of JD constraints |
| API framework | FastAPI | Async, auto-docs, pydantic validation |

---

## Limitations and Future Work

- **LLM reranking**: Adding a lightweight LLM (GPT-4o-mini) as a second-stage reranker on top of FAISS candidates would improve accuracy for ambiguous queries
- **Hybrid search**: BM25 + dense retrieval ensemble for better keyword recall
- **Query expansion**: Extracting skills/requirements via NER before embedding
- **Online learning**: Using train set labels to fine-tune embedding model with triplet loss
