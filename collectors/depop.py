import os
import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

DEPOP_BASE = "https://www.depop.com"
SEARCH_URL = f"{DEPOP_BASE}/search/"


class DepopCollector:
    def __init__(self):
        self.api_key = os.getenv("SCRAPERAPI_KEY")
        if not self.api_key:
            raise ValueError("SCRAPERAPI_KEY must be set in .env")

    def search(self, keyword, limit=24):
        """
        Search Depop listings via ScraperAPI-rendered HTML.
        Returns a list of normalized listing dicts.
        """
        response = requests.get(
            "http://api.scraperapi.com",
            params={
                "api_key": self.api_key,
                "url": f"{SEARCH_URL}?q={keyword}",
                "render": "true",
            },
            timeout=60,
        )
        response.raise_for_status()
        return self._parse(response.text, limit)

    def _parse(self, html, limit):
        soup = BeautifulSoup(html, "lxml")
        product_links = soup.find_all("a", href=re.compile(r"^/products/"))

        results = []
        for a in product_links[:limit]:
            slug = a["href"].strip("/").split("/")[-1]

            # Card container is 3 levels up from the <a>
            card = a.parent.parent.parent

            price_el = card.find("p", attrs={"aria-description": "Price"})
            price_text = price_el.text.strip() if price_el else None
            price = self._parse_price(price_text)

            # Derive title from slug
            title = self._slug_to_title(slug)

            results.append({
                "platform": "depop",
                "listing_id": slug,
                "title": title,
                "price": price,
                "currency": "USD",
                "category": None,
                "condition": None,
                "url": f"{DEPOP_BASE}/products/{slug}/",
                "collected_at": datetime.now(timezone.utc),
            })

        return results

    def _parse_price(self, price_text):
        if not price_text:
            return None
        digits = re.sub(r"[^\d.]", "", price_text)
        try:
            return float(digits)
        except ValueError:
            return None

    def _slug_to_title(self, slug):
        # Strip leading username (up to first '-') and trailing hash (last 4-char segment)
        parts = slug.split("-")
        # Username is the first segment
        # Hash is a short alphanumeric suffix at the end
        if len(parts) > 2:
            parts = parts[1:-1]
        return " ".join(parts).title()
