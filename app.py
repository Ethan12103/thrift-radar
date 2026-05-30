from flask import Flask, render_template, request, jsonify
from analyze import top_keywords, momentum_scores, new_keywords

app = Flask(__name__)

VALID_PLATFORMS = {"grailed", "depop"}

# Keyword → style cluster mapping
STYLE_CLUSTERS = {
    "Denim & Bottoms": {
        "denim", "jeans", "jean", "japanese_denim", "selvedge_denim",
        "cargo_pants", "wide_leg", "straight_leg", "slim_fit", "relaxed_fit",
        "trouser", "chino", "pant", "cord", "corduroy", "shorts",
    },
    "Outerwear": {
        "jacket", "coat", "parka", "anorak", "windbreaker",
        "fleece_jacket", "trucker_jacket", "field_jacket", "bomber_jacket",
        "work_jacket", "chore_coat", "vest",
    },
    "Tops & Knitwear": {
        "shirt", "tee", "sweatshirt", "hoodie", "pullover", "knit",
        "polo", "flannel", "henley_shirt", "overshirt", "crewneck", "sweater",
    },
    "Aesthetics": {
        "gorpcore", "quiet_luxury", "dark_academia", "techwear", "preppy",
        "workwear",
    },
    "Construction": {
        "single_stitch", "double_knee", "military_surplus", "selvedge",
    },
    "Footwear": {
        "boot", "sneaker", "shoe", "loafer", "sandal",
    },
}


def assign_cluster(keyword: str) -> str:
    if keyword.startswith("brand:"):
        return "Brands"
    kw = keyword.lower()
    for cluster, terms in STYLE_CLUSTERS.items():
        if kw in terms:
            return cluster
        for term in terms:
            if term in kw:
                return cluster
    return "Other"


def _platform(req):
    p = req.args.get("platform", "").strip().lower()
    return p if p in VALID_PLATFORMS else None


@app.route("/")
def index():
    platform = _platform(request)
    kw_data = top_keywords(n=30, platform=platform)
    mom_data = momentum_scores(min_recent_count=3, min_baseline_count=1,
                               top_n=20, platform=platform)
    new_data = new_keywords(min_recent_count=3, top_n=10, platform=platform)
    return render_template("index.html",
                           platform=platform or "all",
                           kw_data=kw_data,
                           mom_data=mom_data,
                           new_data=new_data)


@app.route("/api/top-keywords")
def api_top_keywords():
    platform = _platform(request)
    data = top_keywords(n=30, platform=platform)
    labels = [kw for kw, _ in data]
    values = [cnt for _, cnt in data]
    return jsonify({"labels": labels, "values": values})


@app.route("/api/momentum")
def api_momentum():
    platform = _platform(request)
    data = momentum_scores(min_recent_count=3, min_baseline_count=1,
                           top_n=20, platform=platform)
    return jsonify({
        "labels":        [d["keyword"]       for d in data],
        "scores":        [d["score"]         for d in data],
        "freq_momentum": [d["freq_momentum"] for d in data],
        "heat_momentum": [d["heat_momentum"] for d in data],
        "recent_count":  [d["recent_count"]  for d in data],
    })


@app.route("/api/new-keywords")
def api_new_keywords():
    platform = _platform(request)
    return jsonify(new_keywords(min_recent_count=3, top_n=10, platform=platform))


@app.route("/clusters")
def clusters_page():
    platform = _platform(request)
    mom_data = momentum_scores(min_recent_count=3, min_baseline_count=1,
                               top_n=30, platform=platform)
    for item in mom_data:
        item["cluster"] = assign_cluster(item["keyword"])
    return render_template("clusters.html", platform=platform or "all", mom_data=mom_data)


@app.route("/api/clusters")
def api_clusters():
    platform = _platform(request)
    data = momentum_scores(min_recent_count=3, min_baseline_count=1,
                           top_n=30, platform=platform)
    for item in data:
        item["cluster"] = assign_cluster(item["keyword"])
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
