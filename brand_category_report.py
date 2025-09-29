"""Generate a report of product brands per category from the Bond X Lowe's catalog API."""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from typing import DefaultDict, Dict, Iterable, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.bondxlowes.com/catalog/v3/products"
INCLUDE_PARAMS = ("include[]", "manufacturer_data")
USER_AGENT = "brand-category-reporter/1.0"


def fetch_page(page: int) -> Dict:
    """Fetch a single page of products from the API."""
    query = urlencode({INCLUDE_PARAMS[0]: INCLUDE_PARAMS[1], "currentPage": page})
    request = Request(
        f"{BASE_URL}?{query}",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_brands() -> Dict[Tuple[str, str], Set[str]]:
    """Collect brands grouped by category across all pages."""
    category_brands: DefaultDict[Tuple[str, str], Set[str]] = defaultdict(set)

    page = 1
    while True:
        try:
            payload = fetch_page(page)
        except (HTTPError, URLError) as exc:  # pragma: no cover - network failure handling
            print(f"Failed to fetch page {page}: {exc}", file=sys.stderr)
            raise SystemExit(1)

        products: Iterable[Dict] = payload.get("data", [])
        for product in products:
            category = product.get("category") or {}
            category_id = category.get("id") or "unknown"
            category_name = category.get("name") or "Uncategorized"
            key = (category_id, category_name)

            manufacturer = product.get("manufacturerData") or {}
            brand = manufacturer.get("brand") or "Unknown"
            category_brands[key].add(brand)

        pagination = payload.get("pagination") or {}
        current_page = pagination.get("currentPage", page)
        last_page = pagination.get("lastPage", page)
        if current_page >= last_page:
            break
        page = current_page + 1
        time.sleep(0.1)  # small pause to be polite to the API

    return category_brands


def print_report(category_brands: Dict[Tuple[str, str], Set[str]]) -> None:
    """Print a sorted report of brands present in each category."""
    for (category_id, category_name) in sorted(category_brands, key=lambda item: (item[1].lower(), item[0])):
        brands = sorted(category_brands[(category_id, category_name)], key=str.lower)
        print(f"Category: {category_name} (ID: {category_id})")
        for brand in brands:
            print(f"  - {brand}")
        print()


def main() -> None:
    category_brands = collect_brands()
    print_report(category_brands)


if __name__ == "__main__":
    main()
