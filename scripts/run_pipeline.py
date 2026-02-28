

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run the full SHL recommendation pipeline")
    parser.add_argument(
        "--excel_path",
        default="data/Gen_AI_Dataset__2_.xlsx",
        help="Path to Excel dataset (Train + Test sets)",
    )
    parser.add_argument(
        "--skip_crawl",
        action="store_true",
        help="Skip crawling if data/assessments.json already exists",
    )
    parser.add_argument(
        "--skip_index",
        action="store_true",
        help="Skip index building if data/faiss.index already exists",
    )
    parser.add_argument(
        "--skip_eval",
        action="store_true",
        help="Skip evaluation on train set",
    )
    parser.add_argument(
        "--top_n",
        type=int,
        default=10,
        help="Max recommendations per query",
    )
    args = parser.parse_args()

    
    assessments_path = Path("data/assessments.json")

    if args.skip_crawl and assessments_path.exists():
        logger.info("Skipping crawl — using existing %s", assessments_path)
    else:
        logger.info("=" * 50)
        logger.info("STEP 1: Crawling SHL Product Catalog")
        logger.info("=" * 50)
        from crawler.shl_crawler import crawl, save
        assessments = crawl(skip_detail_pages=False)
        save(assessments)
        logger.info("✅ Step 1 complete: %d assessments saved", len(assessments))

    
    faiss_path = Path("data/faiss.index")

    if args.skip_index and faiss_path.exists():
        logger.info("Skipping index build — using existing %s", faiss_path)
    else:
        logger.info("=" * 50)
        logger.info("STEP 2: Building FAISS Index")
        logger.info("=" * 50)
        from embeddings.index_builder import build_index
        build_index()
        logger.info("✅ Step 2 complete: FAISS index built")

   
    if not args.skip_eval:
        logger.info("=" * 50)
        logger.info("STEP 3: Evaluating on Train-Set (Mean Recall@10)")
        logger.info("=" * 50)
        from evaluation.evaluate import run_evaluation
        run_evaluation(args.excel_path, k=10)
        logger.info("✅ Step 3 complete: Evaluation done")
    else:
        logger.info("Skipping evaluation (--skip_eval)")

    
    logger.info("=" * 50)
    logger.info("STEP 4: Generating Test-Set Predictions")
    logger.info("=" * 50)
    from scripts.generate_test_predictions import generate_predictions
    generate_predictions(args.excel_path, "data/predictions.csv", top_n=args.top_n)
    logger.info(" Step 4 complete: predictions.csv generated")

    print("\n Full pipeline complete!")
    print("   Assessments:   data/assessments.json")
    print("   FAISS index:   data/faiss.index")
    print("   Eval results:  data/eval_results.json")
    print("   Predictions:   data/predictions.csv")
    print("\nTo start the API:")
    print("   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")


if __name__ == "__main__":
    main()
