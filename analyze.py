import re
from collections import Counter, defaultdict

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from db import Session, Listing

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

lemmatizer = WordNetLemmatizer()

# General English stopwords + fashion listing noise
STOPWORDS = set(stopwords.words("english")) | {
    # Sizes
    "xs", "s", "m", "l", "xl", "xxl", "xxxl", "2xl", "3xl", "xsmall",
    "small", "medium", "large", "xlarge", "petite", "plus",
    # Listing noise
    "new", "nwt", "nwot", "nwob", "nos", "used", "good", "great",
    "excellent", "perfect", "nice", "lot", "bundle",
    "men", "mens", "women", "womens", "man", "woman", "unisex", "adult",
    "size", "sz", "fit", "fits", "wear", "worn",
    "free", "shipping", "sold", "price", "firm", "offer",
    "vintage", "rare", "grail", "deadstock",
}

# Fashion-relevant bigrams to preserve as single tokens before tokenizing
BIGRAMS = [
    "cargo pants", "wide leg", "straight leg", "slim fit", "relaxed fit",
    "japanese denim", "selvedge denim", "single stitch", "double knee",
    "military surplus", "gorpcore", "quiet luxury", "dark academia",
    "fleece jacket", "trucker jacket", "field jacket", "bomber jacket",
    "work jacket", "chore coat", "overshirt", "henley shirt",
]


def extract_keywords(text: str) -> list[str]:
    """
    Extract meaningful keywords from a listing title.
    Returns a list of normalized tokens/bigrams.
    """
    if not text:
        return []

    text = text.lower()

    # Pull out known bigrams before tokenizing so they survive as one token
    found_bigrams = []
    for bigram in BIGRAMS:
        if bigram in text:
            found_bigrams.append(bigram.replace(" ", "_"))
            text = text.replace(bigram, "")

    # Strip emojis and punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # Remove standalone numbers and decade tokens
    text = re.sub(r"\b\d{1,4}s?\b", " ", text)

    tokens = word_tokenize(text)
    tokens = [
        lemmatizer.lemmatize(t)
        for t in tokens
        if t not in STOPWORDS and len(t) > 2
    ]

    return tokens + found_bigrams


def get_collection_runs(session) -> list:
    """
    Return sorted list of distinct collection run timestamps.
    Rows from the same run are bucketed by truncating to the nearest hour.
    """
    rows = session.query(Listing.collected_at).distinct().all()
    runs = set()
    for (ts,) in rows:
        if ts:
            runs.add(ts.replace(minute=0, second=0, microsecond=0))
    return sorted(runs)


def keyword_frequencies_by_run(platform: str = None) -> dict:
    """
    Returns {run_timestamp: Counter(keyword -> count)} for all collection runs.
    Optionally filter by platform.
    """
    session = Session()
    runs = get_collection_runs(session)

    result = {}
    for run in runs:
        run_end = run.replace(minute=59, second=59)
        query = session.query(Listing).filter(
            Listing.collected_at >= run,
            Listing.collected_at <= run_end,
        )
        if platform:
            query = query.filter_by(platform=platform)

        counter = Counter()
        for listing in query:
            counter.update(extract_keywords(listing.title or ""))
            if listing.brand and listing.brand not in ("Other", "Vintage", "Japanese Brand"):
                counter.update([f"brand:{listing.brand.lower()}"])

        result[run] = counter

    session.close()
    return result


def top_keywords(n: int = 30, platform: str = None) -> list[tuple]:
    """
    Return the top n keywords by total frequency across all runs.
    """
    freqs = keyword_frequencies_by_run(platform)
    total = Counter()
    for counter in freqs.values():
        total.update(counter)
    return total.most_common(n)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("---- Top keywords across all platforms ----\n")
    for keyword, count in top_keywords(30):
        print(f"  {keyword:<25} {count:>4}")

    print()
    print("---- Keyword frequencies by collection run ----\n")
    freqs = keyword_frequencies_by_run()
    runs = sorted(freqs.keys())
    if len(runs) < 2:
        print("  Need at least 2 collection runs to compare windows.")
    else:
        # Show top 15 from latest run vs previous run
        latest = freqs[runs[-1]]
        previous = freqs[runs[-2]]
        all_keywords = set(latest.keys()) | set(previous.keys())
        top = sorted(all_keywords, key=lambda k: latest.get(k, 0), reverse=True)[:15]

        print(f"  {'keyword':<25} {'prev':>6} {'latest':>6}")
        print(f"  {'-'*25} {'------':>6} {'------':>6}")
        for kw in top:
            prev_count = previous.get(kw, 0)
            latest_count = latest.get(kw, 0)
            arrow = "▲" if latest_count > prev_count else ("▼" if latest_count < prev_count else " ")
            print(f"  {kw:<25} {prev_count:>6} {latest_count:>6}  {arrow}")
