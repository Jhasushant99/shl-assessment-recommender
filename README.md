# SHL Assessment Recommendation System

An intelligent recommendation engine that maps natural language queries and job descriptions to relevant SHL Individual Test Solutions using semantic search (Sentence-BERT + FAISS).

## Live Links

- **Web App:** https://shl-assessment-recommender-fd7y.onrender.com
- **API Endpoint:** https://shl-assessment-recommender-fd7y.onrender.com/recommend
- **Health Check:** https://shl-assessment-recommender-fd7y.onrender.com/health
- **API Docs:** https://shl-assessment-recommender-fd7y.onrender.com/docs

## API Usage

### Health Check
```
GET https://shl-assessment-recommender-fd7y.onrender.com/health
```

### Get Recommendations
```
POST https://shl-assessment-recommender-fd7y.onrender.com/recommend
Content-Type: application/json

{
  "query": "Java developer who collaborates with business teams",
  "top_n": 10
}
```

## Project Structure
```
shl_recommender/
├── crawler/shl_crawler.py
├── embeddings/index_builder.py
├── recommender/engine.py
├── evaluation/evaluate.py
├── api/main.py
├── scripts/
│   ├── run_pipeline.py
│   ├── generate_test_predictions.py
│   └── query_cli.py
└── data/
    ├── assessments.json
    ├── faiss.index
    └── predictions.csv
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Pipeline
```bash
python -m crawler.shl_crawler
python -m embeddings.index_builder
python -m evaluation.evaluate --excel_path data/Gen_AI_Dataset__2_.xlsx
python scripts/generate_test_predictions.py --excel_path data/Gen_AI_Dataset__2_.xlsx
```

## Start API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Tech Stack

- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Vector Search:** FAISS
- **API:** FastAPI
- **Crawler:** BeautifulSoup + requests
- **Evaluation:** Mean Recall@10
