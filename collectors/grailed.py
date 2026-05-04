import os
import requests
from datetime import datetime, timezone

GRAILED_BASE = "https://www.grailed.com"

ALGOLIA_INDEX = "Listing_production"


class GrailedCollector:
    def __init__(self):
        app_id = os.getenv("GRAILED_ALGOLIA_APP_ID", "")
        api_key = os.getenv("GRAILED_ALGOLIA_API_KEY", "")

        if not app_id or not api_key:
            raise ValueError(
                "GRAILED_ALGOLIA_APP_ID and GRAILED_ALGOLIA_API_KEY must be set. "
                "Find them by inspecting network requests on grailed.com."
            )
        self.search_url = (
            f"https://{app_id}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query"
        )
        self.headers = {
            "X-Algolia-Application-Id": app_id,
            "X-Algolia-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def search(self, keyword, limit=20):
        """
        Search Grailed listings via Algolia.
        Returns a list of normalized listing dicts.
        """
        payload = {
            "query": keyword,
            "hitsPerPage": limit,
            "filters": "sold=0",
        }
        response = requests.post(self.search_url, json=payload, headers=self.headers)
        response.raise_for_status()
        hits = response.json().get("hits", [])
        return [self._normalize(hit) for hit in hits]

    def _normalize(self, hit):
        """Map a raw Algolia hit to our standard listing schema."""
        price_i = hit.get("price_i")  # integer price in cents

        return {
            "platform": "grailed",
            "listing_id": str(hit.get("id", hit.get("objectID", ""))),
            "title": hit.get("title"),
            "price": price_i / 100 if price_i is not None else None,
            "currency": "USD",
            "category": hit.get("designer_names"),
            "condition": hit.get("condition"),
            "url": f"{GRAILED_BASE}/listings/{hit.get('id')}",
            "collected_at": datetime.now(timezone.utc),
        }
