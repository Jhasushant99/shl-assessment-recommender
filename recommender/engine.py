

import logging
import re
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from embeddings.index_builder import load_index, MODEL_NAME

logger = logging.getLogger(__name__)

# Domain keywords → test type label prefix
DOMAIN_SIGNALS = {
    "Knowledge & Skills": [
        "java", "python", "sql", "javascript", "coding", "programming", "developer",
        "software", "technical", "c++", "c#", ".net", "react", "angular", "node",
        "data", "analyst", "excel", "ms office", "word", "powerpoint", "accounting",
        "finance", "financial", "excel", "database", "cloud", "aws", "azure",
        "machine learning", "ml", "ai", "engineer", "engineering",
        "html", "css", "typescript", "r ", "rust", "golang", "go ",
        "testing", "qa", "devops", "kubernetes", "docker"
    ],
    "Personality & Behaviour": [
        "personality", "behaviour", "behavior", "collaboration", "collaborate",
        "teamwork", "communication", "leadership", "interpersonal", "stakeholder",
        "culture", "values", "motivation", "soft skill", "emotional", "resilience",
        "attitude", "work style", "competency", "competencies"
    ],
    "Ability & Aptitude": [
        "cognitive", "aptitude", "reasoning", "verbal", "numerical", "logical",
        "critical thinking", "problem solving", "abstract", "spatial", "mental",
        "iq", "intelligence", "thinking", "analytical", "analysis"
    ],
    "Competencies": [
        "competency", "competencies", "360", "management", "leadership",
        "strategic", "executive"
    ],
    "Simulations": [
        "simulation", "situational", "scenario", "sjt", "in-tray", "inbox"
    ],
    "Biodata & Situational Judgement": [
        "situational judgement", "sjt", "biodata", "background", "experience"
    ]
}

MIN_RESULTS = 5
MAX_RESULTS = 10
RETRIEVAL_MULTIPLIER = 4  # Retrieve 4x final count for reranking pool


def _detect_domains(query: str) -> list[str]:
    
    query_lower = query.lower()
    detected = []
    for domain, keywords in DOMAIN_SIGNALS.items():
        if any(kw in query_lower for kw in keywords):
            detected.append(domain)
    return detected


def _extract_duration_constraint(query: str) -> Optional[int]:
    
    match = re.search(
        r"(?:within|less than|under|max(?:imum)?|no more than|completed? in)\s*"
        r"(\d+)\s*(?:minutes?|mins?)",
        query,
        re.IGNORECASE
    )
    if match:
        return int(match.group(1))
    # Also catch: '40 minutes'
    match2 = re.search(r"\b(\d+)\s*(?:minutes?|mins?)\b", query, re.IGNORECASE)
    if match2:
        return int(match2.group(1))
    return None


def _balance_by_domain(
    candidates: list[dict],
    detected_domains: list[str],
    n: int,
) -> list[dict]:
    
    if not detected_domains or len(detected_domains) == 1:
        return candidates[:n]

    # Bucket candidates by their test types
    buckets: dict[str, list[dict]] = {d: [] for d in detected_domains}
    remainder = []

    for cand in candidates:
        types = cand.get("test_types", [])
        placed = False
        for domain in detected_domains:
            if any(domain in t for t in types):
                buckets[domain].append(cand)
                placed = True
                break
        if not placed:
            remainder.append(cand)

    # Allocate slots per domain
    slots_per_domain = max(1, n // len(detected_domains))
    result = []
    seen_urls = set()

    for domain in detected_domains:
        count = 0
        for item in buckets[domain]:
            if item["url"] not in seen_urls and count < slots_per_domain:
                result.append(item)
                seen_urls.add(item["url"])
                count += 1

    # Fill remaining slots from remainder or overflow, by score order
    for item in candidates:
        if len(result) >= n:
            break
        if item["url"] not in seen_urls:
            result.append(item)
            seen_urls.add(item["url"])

    return result[:n]


class SHLRecommender:
    

    def __init__(
        self,
        faiss_path: Optional[Path] = None,
        meta_path: Optional[Path] = None,
        model_name: str = MODEL_NAME,
    ):
        logger.info("Initializing SHLRecommender...")
        self.index, self.meta = load_index(faiss_path, meta_path) if faiss_path else load_index()
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        logger.info("SHLRecommender ready. Index size: %d", self.index.ntotal)

    def recommend(
        self,
        query: str,
        top_n: int = MAX_RESULTS,
        min_n: int = MIN_RESULTS,
    ) -> list[dict]:
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        top_n = max(min_n, min(top_n, MAX_RESULTS))

        # 1. Detect domains and duration constraint
        detected_domains = _detect_domains(query)
        max_duration = _extract_duration_constraint(query)

        logger.info(
            "Query domains: %s | Duration constraint: %s min",
            detected_domains, max_duration
        )

        # 2. Embed query
        query_vec = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

        # 3. FAISS search — retrieve large pool for reranking
        pool_size = min(top_n * RETRIEVAL_MULTIPLIER, self.index.ntotal)
        scores, indices = self.index.search(query_vec, pool_size)

        # 4. Build candidate list
        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            item = dict(self.meta[idx])
            item["_score"] = float(score)
            candidates.append(item)

        # 5. Apply duration filter if requested
        if max_duration is not None:
            filtered = [
                c for c in candidates
                if c.get("duration") is None or c["duration"] <= max_duration
            ]
            # Only apply filter if it doesn't remove too many results
            if len(filtered) >= min_n:
                candidates = filtered
            else:
                logger.warning(
                    "Duration filter (%d min) left only %d candidates; relaxing filter.",
                    max_duration, len(filtered)
                )

        # 6. Domain-balanced reranking
        results = _balance_by_domain(candidates, detected_domains, top_n)

        # 7. Ensure minimum
        if len(results) < min_n:
            # Top up from remaining candidates by score
            seen = {r["url"] for r in results}
            for c in candidates:
                if c["url"] not in seen:
                    results.append(c)
                    seen.add(c["url"])
                if len(results) >= min_n:
                    break

        logger.info("Returning %d recommendations for query.", len(results))
        return results[:top_n]
