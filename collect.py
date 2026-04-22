import os
from dotenv import load_dotenv
from db import init_db, Session, Listing
from collectors.ebay import EbayCollector

load_dotenv()

# Target keywords to track
KEYWORDS = [
    "vintage",
    "gorpcore",
    "japanese denim",
    "selvedge",
    "workwear",
    "military surplus"
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


if __name__ == "__main__":
    print("Initializing database")
    init_db()

    print("Starting collection\n")
    collect_ebay(KEYWORDS)

    print("\nDone.")
