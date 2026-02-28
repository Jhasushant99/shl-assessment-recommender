

import argparse
import logging
import re

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SHLRecommender/1.0)"
}


def fetch_jd_from_url(url: str) -> str:
    
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:5000]  # Truncate to first 5000 chars


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch JD text from URL")
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    text = fetch_jd_from_url(args.url)
    print(text[:500])
