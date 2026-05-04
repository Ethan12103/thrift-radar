import os
import pytest
from unittest.mock import patch, MagicMock
from collectors.ebay import EbayCollector

# Fake credentials so __init__ doesn't raise KeyError
os.environ.setdefault("EBAY_CLIENT_ID", "test_id")
os.environ.setdefault("EBAY_CLIENT_SECRET", "test_secret")
os.environ.setdefault("EBAY_ENV", "sandbox")

# Mock so tests are not relient on eBay being up
FAKE_ITEM = {
    "itemId": "v1|123456|0",
    "title": "Vintage Levi 501 Jeans W32 L30",
    "price": {"value": "45.00", "currency": "USD"},
    "categories": [{"categoryName": "Jeans"}],
    "condition": "Pre-Owned",
    "itemWebUrl": "https://www.ebay.com/itm/123456",
}

FAKE_SEARCH_RESPONSE = {
    "itemSummaries": [FAKE_ITEM],
    "total": 1,
}


@pytest.fixture
def collector():
    return EbayCollector()


def test_normalize_full_item(collector):
    result = collector._normalize(FAKE_ITEM)

    assert result["platform"] == "ebay"
    assert result["listing_id"] == "v1|123456|0"
    assert result["title"] == "Vintage Levi 501 Jeans W32 L30"
    assert result["price"] == "45.00"
    assert result["currency"] == "USD"
    assert result["category"] == "Jeans"
    assert result["condition"] == "Pre-Owned"
    assert result["url"] == "https://www.ebay.com/itm/123456"
    assert result["collected_at"] is not None


def test_normalize_missing_optional_fields(collector):
    """Should not raise when price, categories, or condition are absent"""
    result = collector._normalize({"itemId": "abc", "title": "Some Item"})

    assert result["listing_id"] == "abc"
    assert result["price"] is None
    assert result["currency"] is None
    assert result["category"] is None
    assert result["condition"] is None


def test_search_returns_normalized_listings(collector):
    mock_response = MagicMock()
    mock_response.json.return_value = FAKE_SEARCH_RESPONSE

    # Skip real token fetch by pre-setting the token
    collector._token = "fake_token"

    with patch("collectors.ebay.requests.get", return_value=mock_response):
        results = collector.search("vintage levi", limit=10)

    assert len(results) == 1
    assert results[0]["listing_id"] == "v1|123456|0"


def test_search_empty_results(collector):
    mock_response = MagicMock()
    mock_response.json.return_value = {}  # no itemSummaries key

    collector._token = "fake_token"

    with patch("collectors.ebay.requests.get", return_value=mock_response):
        results = collector.search("some obscure keyword")

    assert results == []


def test_get_token_sets_token(collector):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "my_token_123"}

    with patch("collectors.ebay.requests.post", return_value=mock_response):
        collector._get_token()

    assert collector._token == "my_token_123"
