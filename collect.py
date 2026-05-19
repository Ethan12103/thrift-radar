import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from db import init_db, Session, Listing
from collectors.ebay import EbayCollector
from collectors.grailed import GrailedCollector
from collectors.depop import DepopCollector

load_dotenv()

# Target keywords to track
KEYWORDS = [
    # Aesthetics / movements
    "gorpcore",
    "workwear",
    "military surplus",
    "y2k",
    "archival",
    "vintage",
    "distressed",
    "prep",
    # Item types
    "japanese denim",
    "selvedge",
    "fleece",
    "hbt",
    "overshirt",
    "single stitch",
]


def collect_ebay(keywords):
    collector = EbayCollector()
    session = Session()

    for keyword in keywords:
        print(f"[eBay] Searching: '{keyword}'")
        try:
            listings = collector.search(keyword, limit=50)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        new_count = 0
        for item in listings:
            # Skip if we already have this listing
            exists = session.query(Listing).filter_by(
                platform="ebay", listing_id=item["listing_id"]
            ).first()
            if exists:
                continue

            session.add(Listing(**item))
            new_count += 1

        session.commit()
        print(f"  Saved {new_count} new listings.")

    session.close()


def collect_grailed(keywords, run_time):
    collector = GrailedCollector()
    session = Session()

    for keyword in keywords:
        print(f"[Grailed] Searching: '{keyword}'")
        try:
            listings = collector.search(keyword, limit=20)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        new_count = 0
        for item in listings:
            exists = session.query(Listing).filter_by(
                platform="grailed", listing_id=item["listing_id"]
            ).first()
            if exists:
                continue

            item["collected_at"] = run_time
            session.add(Listing(**item))
            new_count += 1

        session.commit()
        print(f"  Saved {new_count} new listings.")

    session.close()


def collect_depop(keywords, run_time):
    collector = DepopCollector()
    session = Session()

    for keyword in keywords:
        print(f"[Depop] Searching: '{keyword}'")
        try:
            listings = collector.search(keyword, limit=20)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        new_count = 0
        for item in listings:
            exists = session.query(Listing).filter_by(
                platform="depop", listing_id=item["listing_id"]
            ).first()
            if exists:
                continue

            item["collected_at"] = run_time
            session.add(Listing(**item))
            new_count += 1

        session.commit()
        print(f"  Saved {new_count} new listings.")

    session.close()


if __name__ == "__main__":
    print("Initializing database")
    init_db()

    run_time = datetime.now(timezone.utc)
    print(f"Starting collection (run_time={run_time.isoformat()})\n")
    collect_ebay(KEYWORDS)
    collect_grailed(KEYWORDS, run_time)
    collect_depop(KEYWORDS, run_time)

    print("\nDone.")
