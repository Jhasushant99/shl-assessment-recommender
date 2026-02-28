

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd

from recommender.engine import SHLRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_train_set(excel_path: str | Path) -> dict[str, list[str]]:
   
    df = pd.read_excel(excel_path, sheet_name="Train-Set")
    df.columns = [c.strip() for c in df.columns]

    if "Query" not in df.columns or "Assessment_url" not in df.columns:
        raise ValueError(
            f"Train-Set must have 'Query' and 'Assessment_url' columns. "
            f"Found: {list(df.columns)}"
        )

    query_to_relevant = defaultdict(list)
    for _, row in df.iterrows():
        q = str(row["Query"]).strip()
        url = str(row["Assessment_url"]).strip()
        if q and url and url != "nan":
            # Normalize URL: strip trailing slash for consistent comparison
            url_norm = url.rstrip("/")
            query_to_relevant[q].append(url_norm)

    logger.info("Loaded %d unique queries from Train-Set", len(query_to_relevant))
    return dict(query_to_relevant)


def recall_at_k(predicted_urls: list[str], relevant_urls: list[str], k: int) -> float:
   
    if not relevant_urls:
        return 0.0

    top_k = set(u.rstrip("/") for u in predicted_urls[:k])
    relevant = set(u.rstrip("/") for u in relevant_urls)

    return len(top_k & relevant) / len(relevant)


def mean_recall_at_k(
    recommender: SHLRecommender,
    query_to_relevant: dict[str, list[str]],
    k: int = 10,
) -> tuple[float, dict[str, float]]:
    
    per_query = {}

    for query, relevant_urls in query_to_relevant.items():
        try:
            results = recommender.recommend(query, top_n=k)
            predicted_urls = [r["url"] for r in results]
        except Exception as exc:
            logger.error("Recommendation failed for query '%s': %s", query[:60], exc)
            predicted_urls = []

        r_at_k = recall_at_k(predicted_urls, relevant_urls, k)
        per_query[query] = r_at_k

        logger.info(
            "Query: '%s...' | Relevant: %d | Predicted: %d | Recall@%d: %.4f",
            query[:60],
            len(relevant_urls),
            len(predicted_urls),
            k,
            r_at_k,
        )

    mean_r = sum(per_query.values()) / len(per_query) if per_query else 0.0
    return mean_r, per_query


def run_evaluation(excel_path: str | Path, k: int = 10) -> None:
    """Full evaluation pipeline."""
    logger.info("=" * 60)
    logger.info("SHL Assessment Recommender — Evaluation")
    logger.info("=" * 60)

    # Load data
    query_to_relevant = load_train_set(excel_path)

    # Initialize recommender
    recommender = SHLRecommender()

    # Compute metrics
    mean_r, per_query = mean_recall_at_k(recommender, query_to_relevant, k=k)

    # Print report
    print("\n" + "=" * 60)
    print(f"EVALUATION RESULTS — Mean Recall@{k}")
    print("=" * 60)
    for query, r_at_k in per_query.items():
        print(f"  [{r_at_k:.4f}] {query[:80]}")
    print("-" * 60)
    print(f"  Mean Recall@{k}: {mean_r:.4f}")
    print("=" * 60)

    # Save results
    output = {
        "k": k,
        "mean_recall_at_k": mean_r,
        "per_query": {q[:80]: v for q, v in per_query.items()},
    }
    results_path = Path(__file__).parent.parent / "data" / "eval_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info("Evaluation results saved to %s", results_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SHL Recommender on Train-Set")
    parser.add_argument(
        "--excel_path",
        default="data/Gen_AI_Dataset__2_.xlsx",
        help="Path to the Excel dataset file",
    )
    parser.add_argument("--k", type=int, default=10, help="Recall@K cutoff (default: 10)")
    args = parser.parse_args()

    run_evaluation(args.excel_path, k=args.k)
