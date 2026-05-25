from flask import Flask, render_template, request, jsonify
from analyze import top_keywords, momentum_scores, new_keywords

app = Flask(__name__)

VALID_PLATFORMS = {"grailed", "depop"}


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


if __name__ == "__main__":
    app.run(debug=True)
