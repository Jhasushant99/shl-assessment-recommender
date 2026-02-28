# SHL Assessment Recommendation System

An intelligent recommendation engine that maps natural language queries and job descriptions to relevant SHL Individual Test Solutions using semantic search (Sentence-BERT + FAISS).

---

## Project Structure

```
shl_recommender/
├── crawler/
│   ├── __init__.py
│   └── shl_crawler.py          # Scrapes SHL product catalog
├── embeddings/
│   ├── __init__.py
│   └── index_builder.py        # Builds FAISS index from scraped data
├── recommender/
│   ├── __init__.py
│   └── engine.py               # Core recommendation logic
├── evaluation/
│   ├── __init__.py
│   └── evaluate.py             # Mean Recall@K evaluation on Train-Set
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI endpoints
├── scripts/
│   ├── __init__.py
│   ├── run_pipeline.py         # End-to-end pipeline runner
│   ├── generate_test_predictions.py  # Produces submission CSV
│   ├── query_cli.py            # Interactive CLI for testing
│   ├── fetch_url_jd.py         # Fetch JD text from URL
│   └── generate_mock_data.py   # Mock data for offline testing
├── data/                       # Created at runtime
│   ├── assessments.json        # Crawled catalog data
│   ├── faiss.index             # FAISS vector index
│   ├── index_meta.json         # Assessment metadata aligned with index
│   ├── eval_results.json       # Evaluation output
│   └── predictions.csv         # Test set submission file
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Copy Dataset

```bash
mkdir -p data
cp /path/to/Gen_AI_Dataset__2_.xlsx data/
```

---

## Running Each Step

### Step 1 – Crawl SHL Catalog (REQUIRED)

```bash
python -m crawler.shl_crawler
```

- Crawls `https://www.shl.com/solutions/products/product-catalog/`
- Extracts only "Individual Test Solutions" (ignores Pre-packaged Job Solutions)
- **Raises an error if < 377 assessments are found**
- Saves to `data/assessments.json`
- Takes ~15–30 minutes depending on network speed

### Step 2 – Build FAISS Index

```bash
python -m embeddings.index_builder
```

- Loads `data/assessments.json`
- Generates Sentence-BERT embeddings (`all-MiniLM-L6-v2`)
- Builds and saves FAISS `IndexFlatIP` (cosine similarity)
- Output: `data/faiss.index` + `data/index_meta.json`

### Step 3 – Evaluate on Train Set

```bash
python -m evaluation.evaluate \
    --excel_path data/Gen_AI_Dataset__2_.xlsx \
    --k 10
```

- Loads the labelled `Train-Set` sheet
- Computes Recall@10 per query and Mean Recall@10
- Saves results to `data/eval_results.json`

### Step 4 – Generate Test Set Predictions (Submission CSV)

```bash
python scripts/generate_test_predictions.py \
    --excel_path data/Gen_AI_Dataset__2_.xlsx \
    --output_path data/predictions.csv \
    --top_n 10
```

- Processes all 9 queries in `Test-Set`
- Outputs `data/predictions.csv` in the required format:
  ```
  Query,Assessment_url
  Query1,URL1
  Query1,URL2
  ...
  ```

### Step 5 – Run the API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Test Health Endpoint
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

#### Test Recommend Endpoint
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "I am hiring for Java developers who can also collaborate effectively with my business teams."}'
```

---

## Full Pipeline (One Command)

```bash
python scripts/run_pipeline.py \
    --excel_path data/Gen_AI_Dataset__2_.xlsx
```

To skip crawling if you already have `data/assessments.json`:
```bash
python scripts/run_pipeline.py \
    --excel_path data/Gen_AI_Dataset__2_.xlsx \
    --skip_crawl
```

---

## Interactive CLI Testing

```bash
python scripts/query_cli.py --query "Java developer who collaborates with business teams"
python scripts/query_cli.py  # interactive mode
python scripts/query_cli.py --url "https://example.com/job-description"
```

---

## API Response Format

`POST /recommend` returns:
```json
{
  "recommended_assessments": [
    {
      "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
      "name": "Python (New)",
      "adaptive_support": "No",
      "description": "Multi-choice test measuring Python knowledge...",
      "duration": 11,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"]
    }
  ]
}
```

---

## Design Choices

### Embedding Model: `all-MiniLM-L6-v2`
- 384-dimensional embeddings
- Fast inference (CPU-friendly)
- Strong semantic similarity for short to medium text
- Pretrained on diverse text including job-related content

### Vector Search: FAISS `IndexFlatIP`
- Exact inner product search (cosine similarity after L2 normalization)
- No approximation error — important for correctness
- Scales to 377+ assessments easily on CPU

### Document Construction
Each assessment is embedded as: `name | name | test_types | description[:500] | duration`
- Name repeated twice to boost title matching
- Type labels help route queries like "cognitive test" → Ability & Aptitude

### Domain Balancing
- Query analyzed for domain signals (Java/Python → K, personality/collaboration → P)
- When multiple domains detected, proportional slot allocation
- Fallback to pure score order for single-domain queries

### Duration Filtering
- Regex extracts duration constraints from query ("completed in 40 minutes")
- Filter relaxed if it would produce < 5 results

### Evaluation: Mean Recall@10
- Official metric from the assignment spec
- URL comparison is normalized (trailing slash stripped)

---

## Offline Testing (No Internet)

If you cannot crawl the live SHL catalog:

```bash
# Generate a small mock dataset for testing the pipeline
python scripts/generate_mock_data.py
python -m embeddings.index_builder
python -m evaluation.evaluate --excel_path data/Gen_AI_Dataset__2_.xlsx
```

⚠️ Mock data has ~50 assessments. The real submission requires crawling 377+.
