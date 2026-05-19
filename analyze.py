import re
from collections import Counter

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
    # Generic descriptors that aren't trend signals
    "fabric", "material", "color", "style", "design", "pattern",
    "american", "japanese", "korean", "german", "italian", "british",
    "california", "western", "eastern", "classic", "original",
    "pile", "fade", "faded",
    # Japanese store/location words that slip through brand names
    "zai", "aoyama", "shibuya", "harajuku",
}

# Multi-word fashion terms to preserve as single tokens
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
    # Remove standalone numbers and decade tokens (90s, 2000s, 1996, etc.)
    text = re.sub(r"\b\d{1,4}s?\b", " ", text)

    tokens = word_tokenize(text)
    tokens = [
        lemmatizer.lemmatize(t)
        for t in tokens
        if t not in STOPWORDS and len(t) > 2
    ]

    return tokens + found_bigrams


def _collect_run_data(session, run_start, run_end, platform=None) -> dict:
    """
    For a single collection window, return:
      freq       — Counter of keyword raw occurrence counts
      heat_sum   — Counter of summed heat scores per keyword (Grailed only)
      heat_count — Counter of how many listings with heat contain each keyword
    """
    query = session.query(Listing).filter(
        Listing.collected_at >= run_start,
        Listing.collected_at <= run_end,
    )
    if platform:
        query = query.filter_by(platform=platform)

    freq = Counter()
    heat_sum = Counter()
    heat_count = Counter()

    for listing in query:
        keywords = extract_keywords(listing.title or "")
        # Also treat brand as a keyword signal (exclude generic labels)
        if listing.brand and listing.brand not in ("Other", "Vintage", "Japanese Brand"):
            keywords.append(f"brand:{listing.brand.lower()}")

        freq.update(keywords)

        if listing.heat:
            for kw in keywords:
                heat_sum[kw] += listing.heat
                heat_count[kw] += 1

    return {"freq": freq, "heat_sum": heat_sum, "heat_count": heat_count}


def keyword_frequencies_by_run(platform: str = None) -> dict:
    """
    Returns {run_timestamp: {freq: Counter, heat: Counter}} for all collection runs.
    Runs are bucketed by hour so that per-row microsecond timestamps are grouped.
    """
    session = Session()
    rows = session.query(Listing.collected_at).all()

    # Bucket each row into an hourly run slot
    run_slots = set()
    for (ts,) in rows:
        if ts:
            run_slots.add(ts.replace(minute=0, second=0, microsecond=0))

    result = {}
    for run in sorted(run_slots):
        run_end = run.replace(minute=59, second=59)
        result[run] = _collect_run_data(session, run, run_end, platform)

    session.close()
    return result


def _avg_heat(data: dict, kw: str) -> float:
    """Average heat score per listing for a keyword within a run's data."""
    count = data["heat_count"].get(kw, 0)
    return data["heat_sum"].get(kw, 0) / count if count else 0.0


def top_keywords(n: int = 30, platform: str = None) -> list[tuple]:
    """Return the top n keywords by total raw frequency across all runs."""
    freqs = keyword_frequencies_by_run(platform)
    total = Counter()
    for data in freqs.values():
        total.update(data["freq"])
    return total.most_common(n)


def momentum_scores(min_recent_count: int = 3, min_baseline_count: int = 1,
                    top_n: int = 20, platform: str = None) -> list[dict]:
    """
    Compute a momentum score for each keyword by comparing its normalized
    frequency in the most recent collection window against the rolling baseline
    of all prior windows.

    Score formula:
        freq_momentum  = recent_rate / smoothed_baseline_rate (Laplace)
        heat_momentum  = (recent_avg_heat + 1) / (baseline_avg_heat + 1), capped at 10
        score          = 0.6 * freq_momentum + 0.4 * heat_momentum

    freq_momentum is weighted higher since heat is only available for Grailed.
    A score > 1 means the keyword is appearing more than the baseline.

    Only keywords present in at least one baseline window are scored here.
    Truly new keywords are returned by new_keywords().

    Returns a list of dicts sorted by score descending
    """
    runs_data = keyword_frequencies_by_run(platform)
    runs = sorted(runs_data.keys())

    if len(runs) < 2:
        return []

    latest = runs_data[runs[-1]]
    baseline_runs = [runs_data[r] for r in runs[:-1]]

    latest_freq_total = sum(latest["freq"].values()) or 1

    # Candidates: must meet recent count threshold and appear in the baseline.
    candidates = {
        kw for kw, cnt in latest["freq"].items()
        if cnt >= min_recent_count
        and sum(data["freq"].get(kw, 0) for data in baseline_runs) >= min_baseline_count
    }

    # Laplace smoothing constant: added to both numerator and denominator so
    # keywords absent from the baseline don't produce infinite momentum.
    baseline_freq_total = sum(sum(data["freq"].values()) for data in baseline_runs) or 1
    vocab_size = len(candidates)
    alpha = 1

    scores = []
    for kw in candidates:
        # Frequency momentum
        recent_rate = latest["freq"][kw] / latest_freq_total
        baseline_kw_freq = sum(data["freq"].get(kw, 0) for data in baseline_runs)
        smoothed_baseline_rate = (baseline_kw_freq + alpha) / (baseline_freq_total + alpha * vocab_size)
        freq_momentum = recent_rate / smoothed_baseline_rate

        # Heat momentum: compare average heat per listing
        # Smoothed with +1 so Depop listings (heat=None) don't produce zeros.
        # Capped at 10x
        recent_avg_heat = _avg_heat(latest, kw)
        baseline_avg_heat = sum(_avg_heat(data, kw) for data in baseline_runs) / len(baseline_runs)
        heat_momentum = min((recent_avg_heat + 1) / (baseline_avg_heat + 1), 10.0)

        # Combined: freq weighted higher since heat is Grailed only
        score = 0.6 * freq_momentum + 0.4 * heat_momentum

        scores.append({
            "keyword": kw,
            "score": round(score, 2),
            "freq_momentum": round(freq_momentum, 2),
            "heat_momentum": round(heat_momentum, 2),
            "recent_count": latest["freq"][kw],
        })

    return sorted(scores, key=lambda x: x["score"], reverse=True)[:top_n]


def new_keywords(min_recent_count: int = 3, top_n: int = 10, platform: str = None) -> list[dict]:
    """
    Return keywords that appear in the latest window but not in any baseline window.
    Could be potentially emerging terms.
    """
    runs_data = keyword_frequencies_by_run(platform)
    runs = sorted(runs_data.keys())
    if len(runs) < 2:
        return []

    latest = runs_data[runs[-1]]
    baseline_runs = [runs_data[r] for r in runs[:-1]]

    results = []
    for kw, cnt in latest["freq"].items():
        if cnt < min_recent_count:
            continue
        baseline_total = sum(data["freq"].get(kw, 0) for data in baseline_runs)
        if baseline_total == 0:
            results.append({"keyword": kw, "recent_count": cnt})

    return sorted(results, key=lambda x: x["recent_count"], reverse=True)[:top_n]


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("---- Top keywords (all time) ----\n")
    for keyword, count in top_keywords(20):
        print(f"  {keyword:<25} {count:>4}")

    print()
    print("---- Momentum scores (accelerating keywords) ----\n")
    scores = momentum_scores(min_recent_count=3, min_baseline_count=1, top_n=20)

    if not scores:
        print("  Need at least 2 collection runs to compute momentum.")
    else:
        print(f"  {'keyword':<25} {'score':>6}  {'freq_mom':>8}  {'heat_mom':>8}  {'n':>4}")
        print(f"  {'-'*25} {'------':>6}  {'--------':>8}  {'--------':>8}  {'----':>4}")
        for s in scores:
            print(
                f"  {s['keyword']:<25} {s['score']:>6.2f}"
                f"  {s['freq_momentum']:>8.2f}  {s['heat_momentum']:>8.2f}"
                f"  {s['recent_count']:>4}"
            )

    print()
    print("---- New keywords (not seen in baseline) ----\n")
    for kw in new_keywords(min_recent_count=3, top_n=10):
        print(f"  {kw['keyword']:<25} n={kw['recent_count']}")
