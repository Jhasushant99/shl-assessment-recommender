

import json
import time
import logging
import re
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.shl.com"
CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/"
MIN_REQUIRED_ASSESSMENTS = 377
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 0.5  # seconds between requests
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "assessments.json"


TEST_TYPE_MAP = {
    "A": "Ability & Aptitude",
    "B": "Biodata & Situational Judgement",
    "C": "Competencies",
    "D": "Development & 360",
    "E": "Assessment Exercises",
    "K": "Knowledge & Skills",
    "P": "Personality & Behaviour",
    "S": "Simulations",
}


def _get(url: str, retries: int = 3) -> Optional[requests.Response]:
    
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            logger.warning("Attempt %d failed for %s: %s", attempt + 1, url, exc)
            time.sleep(2 ** attempt)
    logger.error("All retries exhausted for %s", url)
    return None


def _parse_test_type_badges(tag) -> list[str]:
    
    badges = tag.find_all("span", class_=re.compile(r"product-catalogue.*type", re.I))
    if not badges:
        # Try generic badge pattern used in SHL catalog rows
        badges = tag.find_all("span", attrs={"class": lambda c: c and "type" in c.lower()})
    letters = [b.get_text(strip=True) for b in badges if b.get_text(strip=True) in TEST_TYPE_MAP]
    return [TEST_TYPE_MAP[l] for l in letters]


def _scrape_assessment_detail(url: str) -> dict:
    
    detail = {
        "description": "",
        "duration": None,
        "remote_support": "No",
        "adaptive_support": "No",
        "test_types": [],
    }
    resp = _get(url)
    if resp is None:
        return detail

    soup = BeautifulSoup(resp.text, "lxml")

   
    # SHL uses various containers; try multiple selectors
    for sel in [
        ".product-hero__description",
        ".product-description",
        "[class*='description']",
        "article p",
        ".hero p",
    ]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 30:
            detail["description"] = el.get_text(separator=" ", strip=True)
            break

    # Fallback: first substantial <p> in main content
    if not detail["description"]:
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 60:
                detail["description"] = text
                break

    
    full_text = soup.get_text(separator=" ")
    duration_match = re.search(
        r"(\d+)\s*(?:minutes?|mins?)", full_text, re.IGNORECASE
    )
    if duration_match:
        detail["duration"] = int(duration_match.group(1))

   
    # SHL pages typically list these as key-value pairs
    if re.search(r"remote\s+testing.*?yes", full_text, re.IGNORECASE):
        detail["remote_support"] = "Yes"
    if re.search(r"adaptive.*?yes|yes.*?adaptive", full_text, re.IGNORECASE):
        detail["adaptive_support"] = "Yes"

    # --- Test types from detail page badges ---
    badge_letters = re.findall(r'\b([ABCDEKPS])\b', full_text)
    found_types = list(dict.fromkeys(
        TEST_TYPE_MAP[l] for l in badge_letters if l in TEST_TYPE_MAP
    ))
    if found_types:
        detail["test_types"] = found_types

    return detail


def _parse_catalog_page(url: str) -> tuple[list[dict], Optional[str]]:
    
    resp = _get(url)
    if resp is None:
        return [], None

    soup = BeautifulSoup(resp.text, "lxml")
    assessments = []

    
    rows = soup.select("tr.js-product-row, .product-catalogue__row, [data-href*='product-catalog']")

    if not rows:
        # Fallback: find all links to product detail pages
        links = soup.select("a[href*='/product-catalog/view/']")
        for link in links:
            href = link.get("href", "")
            full_url = href if href.startswith("http") else BASE_URL + href
            name = link.get_text(strip=True)
            if name:
                assessments.append({
                    "name": name,
                    "url": full_url,
                    "test_types_raw": [],
                })
    else:
        for row in rows:
            link = row.select_one("a[href*='/product-catalog/view/']")
            if not link:
                continue
            href = link.get("href", "")
            full_url = href if href.startswith("http") else BASE_URL + href
            name = link.get_text(strip=True)
            test_types = _parse_test_type_badges(row)
            assessments.append({
                "name": name,
                "url": full_url,
                "test_types_raw": test_types,
            })

    # Next page
    next_link = soup.select_one("a[rel='next'], .pagination__next a, a.next")
    if not next_link:
        # Try finding pagination by text
        next_link = soup.find("a", string=re.compile(r"next", re.I))
    next_url = None
    if next_link:
        href = next_link.get("href", "")
        if href:
            next_url = href if href.startswith("http") else BASE_URL + href

    return assessments, next_url


def _get_individual_test_catalog_url(base_url: str) -> str:
   
    resp = _get(base_url)
    if resp is None:
        raise RuntimeError(f"Cannot load catalog base URL: {base_url}")

    soup = BeautifulSoup(resp.text, "lxml")

    # Look for a tab/link labeled 'Individual Test Solutions'
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if "individual" in text.lower() and "test" in text.lower():
            href = a["href"]
            return href if href.startswith("http") else BASE_URL + href

    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "type=1" in href or "individual" in href.lower():
            return href if href.startswith("http") else BASE_URL + href

    # Default: the catalog URL with type filter for individual solutions
    # Based on SHL's typical URL pattern
    return CATALOG_URL + "?type=1"


def crawl(skip_detail_pages: bool = False) -> list[dict]:
    
    logger.info("Starting SHL catalog crawl...")

    # Step 1: Locate Individual Test Solutions URL
    individual_url = _get_individual_test_catalog_url(CATALOG_URL)
    logger.info("Individual Test Solutions URL: %s", individual_url)

    # Step 2: Paginate through all listing pages
    all_raw: list[dict] = []
    current_url = individual_url
    page_num = 1

    while current_url:
        logger.info("Crawling listing page %d: %s", page_num, current_url)
        page_assessments, next_url = _parse_catalog_page(current_url)
        logger.info("  Found %d assessments on page %d", len(page_assessments), page_num)
        all_raw.extend(page_assessments)
        current_url = next_url
        page_num += 1
        time.sleep(REQUEST_DELAY)

    # Deduplicate by URL
    seen_urls = set()
    unique_raw = []
    for a in all_raw:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique_raw.append(a)

    logger.info("Total unique assessments found in listing: %d", len(unique_raw))

    # Step 3: Validate minimum count
    if len(unique_raw) < MIN_REQUIRED_ASSESSMENTS:
        # Try alternate catalog URL approaches before failing
        logger.warning(
            "Only found %d assessments via primary method. Trying alternate approach...",
            len(unique_raw)
        )
        # Try paginated URL pattern
        additional = _crawl_paginated(CATALOG_URL)
        for a in additional:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                unique_raw.append(a)
        logger.info("After alternate approach: %d assessments", len(unique_raw))

    if len(unique_raw) < MIN_REQUIRED_ASSESSMENTS:
        raise ValueError(
            f"CRAWL FAILED: Only {len(unique_raw)} individual assessments found. "
            f"Required: {MIN_REQUIRED_ASSESSMENTS}. "
            "Check that the SHL catalog is accessible and pagination is working correctly."
        )

    # Step 4: Scrape detail pages for each assessment
    final_assessments = []
    for i, raw in enumerate(unique_raw):
        logger.info(
            "Scraping detail page %d/%d: %s",
            i + 1, len(unique_raw), raw["name"]
        )
        if skip_detail_pages:
            detail = {
                "description": "",
                "duration": None,
                "remote_support": "No",
                "adaptive_support": "No",
                "test_types": raw.get("test_types_raw", []),
            }
        else:
            detail = _scrape_assessment_detail(raw["url"])
            # Merge test types from listing + detail page
            combined_types = list(dict.fromkeys(
                raw.get("test_types_raw", []) + detail.get("test_types", [])
            ))
            detail["test_types"] = combined_types
            time.sleep(REQUEST_DELAY)

        assessment = {
            "name": raw["name"],
            "url": raw["url"],
            "description": detail["description"],
            "duration": detail["duration"],
            "remote_support": detail["remote_support"],
            "adaptive_support": detail["adaptive_support"],
            "test_types": detail["test_types"],
        }
        final_assessments.append(assessment)

    logger.info("Crawl complete. Total assessments: %d", len(final_assessments))
    return final_assessments


def _crawl_paginated(base_url: str) -> list[dict]:
    
    results = []
    seen_urls = set()
    step = 12
    start = 0
    consecutive_empty = 0

    while consecutive_empty < 3:
        url = f"{base_url}?start={start}&type=1"
        logger.info("Paginated crawl: start=%d", start)
        resp = _get(url)
        if resp is None:
            consecutive_empty += 1
            start += step
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select("a[href*='/product-catalog/view/']")
        new_count = 0

        for link in links:
            href = link.get("href", "")
            full_url = href if href.startswith("http") else BASE_URL + href
            name = link.get_text(strip=True)
            if name and full_url not in seen_urls:
                seen_urls.add(full_url)
                test_types = _parse_test_type_badges(link.parent or link)
                results.append({
                    "name": name,
                    "url": full_url,
                    "test_types_raw": test_types,
                })
                new_count += 1

        if new_count == 0:
            consecutive_empty += 1
        else:
            consecutive_empty = 0

        start += step
        time.sleep(REQUEST_DELAY)

    return results


def save(assessments: list[dict], path: Path = OUTPUT_PATH) -> None:
    """Persist assessments to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d assessments to %s", len(assessments), path)


def load(path: Path = OUTPUT_PATH) -> list[dict]:
    """Load assessments from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    assessments = crawl(skip_detail_pages=False)
    save(assessments)
    print(f"\n Crawl complete: {len(assessments)} assessments saved to {OUTPUT_PATH}")
