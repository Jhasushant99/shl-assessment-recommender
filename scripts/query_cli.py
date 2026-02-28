

import argparse
import logging
import sys

logging.basicConfig(level=logging.WARNING)


def print_results(results: list[dict]) -> None:
    print(f"\n{'='*70}")
    print(f"  {len(results)} Recommendations")
    print(f"{'='*70}")
    for i, r in enumerate(results, 1):
        types = ", ".join(r.get("test_types", [])) or "N/A"
        duration = f"{r['duration']} min" if r.get("duration") else "N/A"
        print(f"\n  {i}. {r['name']}")
        print(f"     Type:     {types}")
        print(f"     Duration: {duration}")
        print(f"     URL:      {r['url']}")
        if r.get("description"):
            desc = r["description"][:120] + "..." if len(r["description"]) > 120 else r["description"]
            print(f"     Desc:     {desc}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Query SHL Recommender")
    parser.add_argument("--query", help="Query or JD text")
    parser.add_argument("--top_n", type=int, default=10)
    parser.add_argument("--url", help="Fetch JD from URL instead of --query")
    args = parser.parse_args()

    from recommender.engine import SHLRecommender
    recommender = SHLRecommender()

    if args.url:
        from scripts.fetch_url_jd import fetch_jd_from_url
        query = fetch_jd_from_url(args.url)
        print(f"Fetched JD text ({len(query)} chars)")
    elif args.query:
        query = args.query
    else:
        # Interactive mode
        print("SHL Assessment Recommender (type 'quit' to exit)\n")
        while True:
            try:
                query = input("Enter query or JD text: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if query.lower() in ("quit", "exit", "q"):
                break
            if not query:
                continue
            results = recommender.recommend(query, top_n=args.top_n)
            print_results(results)
        return

    results = recommender.recommend(query, top_n=args.top_n)
    print_results(results)


if __name__ == "__main__":
    main()
