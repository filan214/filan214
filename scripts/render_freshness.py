"""Show the timestamps actually recorded by each independent data collector."""
from common import DATA, read_json, run
from render_build_spotlight import sync_label
from svg import chrome, rect, save, svg, text


def render(builds, stream, highlights, contributions, languages):
    body = chrome(860, 250, "sources --inspect", "DATA SOURCES & FRESHNESS")
    body += text(28, 80, "Public data. Visible provenance.", "bold", 22)
    body += rect(663, 57, 169, 30, "panel", 15)
    body += text(747, 77, "HOURLY · :17", "cyan bold", 11, extra='text-anchor="middle"')
    rows = [("01 / PROJECTS", builds), ("02 / PUSH STREAM", stream), ("03 / SPOTLIGHTS", highlights)]
    for i, (label, snapshot) in enumerate(rows):
        x = 28+i*274
        body += f'<g class="enter" style="animation-delay:{i*.12}s">'
        body += rect(x, 104, 256, 64, "panel", 8)
        body += text(x+14, 128, label, "cyan bold", 10)
        body += text(x+14, 151, sync_label(snapshot), "", 10)
        body += '</g>'
    body += text(28, 194, "Calendar as of " + contributions["as_of"], "muted", 10)
    body += text(832, 194, "Languages snapshot " + languages["as_of"], "muted", 10, extra='text-anchor="end"')
    body += '<path d="M28 208H832" class="line"/>'
    body += text(28, 231, "GitHub → fetched snapshot → SVG + README", "muted", 10)
    body += text(832, 231, "Sources & refresh details below ↓", "cyan", 10, extra='text-anchor="end"')
    desc = ("Scheduled hourly at minute 17, plus pushes to main and manual refresh. "
            + "; ".join(label + " fetched " + snapshot["fetched_at"] for label, snapshot in rows)
            + f". Contributions as of {contributions['as_of']}; language snapshot {languages['as_of']}. "
            + "These are recorded snapshot times, not a live connection. Schedules, GitHub processing, and image caches can delay updates. "
            + "A failed workflow does not publish a new snapshot.")
    return svg(860, 250, "Data sources and freshness — recorded sync times", desc, body)


def from_files():
    return render(*(read_json(DATA / name) for name in
                    ("builds.json", "commit-stream.json", "highlights.json", "contributions.json", "languages.json")))


if __name__ == "__main__":
    run(lambda: save("data-freshness.svg", from_files()))
