

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
DATA_DIR = Path(__file__).parent.parent / "data"
ASSESSMENTS_PATH = DATA_DIR / "assessments.json"
FAISS_INDEX_PATH = DATA_DIR / "faiss.index"
META_PATH = DATA_DIR / "index_meta.json"


def _build_document(assessment: dict) -> str:
    
    parts = []

    name = assessment.get("name", "").strip()
    if name:
        
        parts.append(name)
        parts.append(name)

    test_types = assessment.get("test_types", [])
    if test_types:
        parts.append("Test type: " + ", ".join(test_types))

    description = assessment.get("description", "").strip()
    if description:
        
        parts.append(description[:500])

    duration = assessment.get("duration")
    if duration:
        parts.append(f"Duration: {duration} minutes")

    return " | ".join(parts)


def build_index(
    assessments_path: Path = ASSESSMENTS_PATH,
    faiss_path: Path = FAISS_INDEX_PATH,
    meta_path: Path = META_PATH,
    model_name: str = MODEL_NAME,
) -> tuple[faiss.Index, list[dict]]:
    
    logger.info("Loading assessments from %s", assessments_path)
    with open(assessments_path, "r", encoding="utf-8") as f:
        assessments = json.load(f)

    logger.info("Loaded %d assessments", len(assessments))
    logger.info("Loading SentenceTransformer model: %s", model_name)
    model = SentenceTransformer(model_name)

    # Build text documents
    documents = [_build_document(a) for a in assessments]

    logger.info("Generating embeddings...")
    embeddings = model.encode(
        documents,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,  # Cosine similarity via inner product
        convert_to_numpy=True,
    )

    dim = embeddings.shape[1]
    logger.info("Embedding dim: %d, Count: %d", dim, len(embeddings))

    # Build FAISS index (Inner Product = cosine similarity when normalized)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))
    logger.info("FAISS index built with %d vectors", index.ntotal)

    # Metadata aligned with index rows
    meta = [
        {
            "name": a.get("name", ""),
            "url": a.get("url", ""),
            "description": a.get("description", ""),
            "duration": a.get("duration"),
            "remote_support": a.get("remote_support", "No"),
            "adaptive_support": a.get("adaptive_support", "No"),
            "test_types": a.get("test_types", []),
        }
        for a in assessments
    ]

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(faiss_path))
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info("FAISS index saved to %s", faiss_path)
    logger.info("Metadata saved to %s", meta_path)

    return index, meta


def load_index(
    faiss_path: Path = FAISS_INDEX_PATH,
    meta_path: Path = META_PATH,
) -> tuple[faiss.Index, list[dict]]:
    """Load FAISS index and metadata from disk."""
    if not faiss_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {faiss_path}. "
            "Run: python -m embeddings.index_builder"
        )
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Index metadata not found at {meta_path}. "
            "Run: python -m embeddings.index_builder"
        )

    index = faiss.read_index(str(faiss_path))
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    logger.info("Loaded FAISS index (%d vectors) and %d metadata entries", index.ntotal, len(meta))
    return index, meta


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    build_index()
    print("\n FAISS index built successfully.")
