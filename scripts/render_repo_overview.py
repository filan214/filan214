"""Account-level repository totals; the recent repositories are README cards."""
from collections import Counter
from datetime import date

from common import DATA, read_json, run
from render_build_spotlight import sync_label
from svg import chrome, save, shorten, svg, text

WIDTH, HEIGHT = 860, 122
STYLES = '.display{font-family:Arial,Helvetica,sans-serif;font-weight:700;letter-spacing:-1px}'


def pushed_recently(repositories, as_of, days=30):
    today = date.fromisoformat(as_of)
    return sum((today - date.fromisoformat(repo["pushed_at"][:10])).days < days for repo in repositories)


def top_language(repositories):
    counts = Counter(repo["language"] for repo in repositories if repo["language"])
    return min(counts.items(), key=lambda row: (-row[1], row[0])) if counts else None


def stat(x, value, label, cls="display"):
    return text(x, 88, shorten(value, 16), cls, 34) + text(x, 108, label, "muted", 10)


def render(data):
    repositories = data["repositories"]
    total = data["profile"]["public_repos"]
    active = pushed_recently(repositories, data["as_of"])
    language = top_language(repositories)
    body = chrome(WIDTH, HEIGHT, "repos --overview", "synced " + sync_label(data))
    body += stat(28, str(total), "public repositories", "display accent")
    body += stat(300, str(active), "pushed in the last 30 days")
    body += stat(572, language[0] if language else "—", f"most common language · {language[1]} repos" if language else "no language reported")
    desc = (f"{total} public repositories, {active} pushed in the last 30 days. "
            f"Most common language: {language[0] if language else 'none reported'}. Snapshot fetched {data['fetched_at']}.")
    return svg(WIDTH, HEIGHT, "Repository overview", desc, body, styles=STYLES)


if __name__ == "__main__":
    run(lambda: save("repo-overview.svg", render(read_json(DATA / "builds.json"))))
