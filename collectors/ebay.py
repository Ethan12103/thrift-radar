import os
import base64
import requests
from datetime import datetime, timezone

SANDBOX_BASE = "https://api.sandbox.ebay.com"
PROD_BASE = "https://api.ebay.com"


class EbayCollector:
    def __init__(self):
        self.client_id = os.environ["EBAY_CLIENT_ID"]
        self.client_secret = os.environ["EBAY_CLIENT_SECRET"]
        self.env = os.getenv("EBAY_ENV", "sandbox")
        self.base_url = SANDBOX_BASE if self.env == "sandbox" else PROD_BASE
        self._token = None

    def _get_token(self):
        """Fetch an OAuth2 app token using client credentials flow"""
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(
            f"{self.base_url}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]

    def _headers(self):
        if not self._token:
            self._get_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

    def search(self, keyword, limit=50):
        """
        Search eBay listings by keyword
        Returns a list of normalized listing dicts
        """
        params = {
            "q": keyword,
            "limit": limit,
            "sort": "newlyListed",
        }

        response = requests.get(
            f"{self.base_url}/buy/browse/v1/item_summary/search",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("itemSummaries", [])
        return [self._normalize(item) for item in items]

    def _normalize(self, item):
        """Map a raw eBay item summary to our standard listing schema"""
        price_info = item.get("price", {})
        categories = item.get("categories", [])

        return {
            "platform": "ebay",
            "listing_id": item.get("itemId", ""),
            "title": item.get("title", ""),
            "price": price_info.get("value"),
            "currency": price_info.get("currency"),
            "category": categories[0].get("categoryName") if categories else None,
            "condition": item.get("condition"),
            "url": item.get("itemWebUrl", ""),
            "collected_at": datetime.now(timezone.utc),
        }
