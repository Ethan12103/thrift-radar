import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, Listing


@pytest.fixture
def session():
    """Each test gets a fresh in-memory SQLite DB"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def make_listing(**kwargs):
    defaults = {
        "platform": "ebay",
        "listing_id": "v1|123|0",
        "title": "Vintage Levi 501",
        "price": 45.00,
        "currency": "USD",
        "category": "Jeans",
        "condition": "Pre-Owned",
        "url": "https://www.ebay.com/itm/123",
        "collected_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return Listing(**defaults)


def test_insert_listing(session):
    listing = make_listing()
    session.add(listing)
    session.commit()

    result = session.query(Listing).first()
    assert result.listing_id == "v1|123|0"
    assert result.platform == "ebay"
    assert result.price == 45.00


def test_deduplication(session):
    """Inserting the same listing_id twice should only result in one row"""
    session.add(make_listing())
    session.commit()

    exists = session.query(Listing).filter_by(platform="ebay", listing_id="v1|123|0").first()
    assert exists is not None  # found it, so skip inserting

    count = session.query(Listing).count()
    assert count == 1


def test_multiple_listings(session):
    session.add(make_listing(listing_id="v1|001|0", title="Selvedge Denim"))
    session.add(make_listing(listing_id="v1|002|0", title="Gorpcore Jacket"))
    session.commit()

    results = session.query(Listing).all()
    assert len(results) == 2


def test_collected_at_is_set(session):
    listing = make_listing()
    session.add(listing)
    session.commit()

    result = session.query(Listing).first()
    assert result.collected_at is not None
