

import argparse
import csv
import logging
from pathlib import Path

import pandas as pd

from recommender.engine import SHLRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_test_queries(excel_path: str | Path) -> list[str]:
    """Load test queries from Test-Set sheet."""
    df = pd.read_excel(excel_path, sheet_name="Test-Set")
    df.columns = [c.strip() for c in df.columns]

    if "Query" not in df.columns:
        raise ValueError(f"Test-Set must have 'Query' column. Found: {list(df.columns)}")

    queries = [str(q).strip() for q in df["Query"].dropna() if str(q).strip()]
    logger.info("Loaded %d test queries", len(queries))
    return queries


def generate_predictions(
    excel_path: str | Path,
    output_path: str | Path,
    top_n: int = 10,
) -> None:
    """Run recommender on all test queries and write CSV."""
    queries = load_test_queries(excel_path)
    recommender = SHLRecommender()

    rows = []
    for i, query in enumerate(queries):
        logger.info("Processing test query %d/%d: '%s...'", i + 1, len(queries), query[:60])
        try:
            results = recommender.recommend(query, top_n=top_n)
            for r in results:
                rows.append({"Query": query, "Assessment_url": r["url"]})
        except Exception as exc:
            logger.error("Failed for query %d: %s", i + 1, exc)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Query", "Assessment_url"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info("✅ Predictions saved to %s (%d rows)", output_path, len(rows))
    print(f"\n✅ Predictions written to: {output_path}")
    print(f"   Total rows: {len(rows)}")
    print(f"   Queries processed: {len(queries)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test set predictions CSV")
    parser.add_argument(
        "--excel_path",
        default="data/Gen_AI_Dataset__2_.xlsx",
        help="Path to Excel dataset",
    )
    parser.add_argument(
        "--output_path",
        default="data/predictions.csv",
        help="Path for output CSV file",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Max recommendations per query (default: 10)",
    )
    args = parser.parse_args()

    generate_predictions(args.excel_path, args.output_path, args.top_n)
