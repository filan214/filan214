"""53 x 7 Sunday-first contribution calendar with a one-shot diagonal reveal."""
from datetime import date, timedelta

from common import DATA, read_json, run
from fetch_contributions import contribution_stats
from svg import chrome, esc, rect, save, svg, text

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def calendar_days(as_of):
    sunday = as_of - timedelta(days=(as_of.weekday() + 1) % 7)
    start = sunday - timedelta(weeks=52)
    return [start + timedelta(days=i) for i in range(53*7)]


def render(data):
    as_of = date.fromisoformat(data["as_of"])
    days = {item["date"]: item for item in data["days"]}
    stats = contribution_stats(data["days"], as_of)
    peak = (stats["best_day"] or {}).get("count", 0)
    body = chrome(860, 310, "git contributions --calendar", "activity / 01")
    body += text(22, 80, f"{stats['total']:,}", "accent large")
    body += text(125, 80, "contributions in the calendar window", "muted small")
    body += text(838, 78, f"as of {as_of.isoformat()} · UTC+07", "muted tiny", extra='text-anchor="end"')
    all_days = calendar_days(as_of)
    previous_month = None
    for i, day in enumerate(all_days):
        column, row = divmod(i, 7)
        x, y = 47 + column*14.6, 118 + row*14.6
        if row == 0 and day.month != previous_month:
            # Avoid a cramped final-column month label.
            if column < 51:
                body += text(x, 108, day.strftime("%b"), "muted tiny")
            previous_month = day.month
        item = days.get(day.isoformat())
        if day > as_of or item is None:
            cls, label = "unknown", f"{day.isoformat()}: {'future' if day > as_of else 'unavailable'}"
        else:
            level = item["level"]
            if item["count"] and item["count"] == peak:
                level = 5
            cls, label = f"p{level}", f"{day.isoformat()}: {item['count']} contributions"
        box = rect(round(x, 2), round(y, 2), 11, 11, cls, 2)
        body += f'<g class="drop" style="animation-delay:{(column+row)*.025:.3f}s"><title>{esc(label)}</title>{box}</g>'
    for row, label in ((1, "M"), (3, "W"), (5, "F")):
        body += text(23, round(127+row*14.6, 2), label, "muted tiny")
    body += text(22, 240, "Less", "muted tiny")
    for i in range(6):
        body += rect(53 + i*16, 231, 11, 11, f"p{i}", 2)
    body += text(155, 240, "More", "muted tiny")
    body += text(838, 240, "dashed = outside available dates", "muted tiny", extra='text-anchor="end"')
    body += '<path d="M20 255H840" class="line"/>'
    best = stats["best_day"]
    footer = [(22, f"current  {stats['current_streak']}d"), (203, f"longest  {stats['longest_streak']}d"), (391, f"best  {best['count'] if best else 0} / {best['date'] if best else '—'}"), (680, f"this month  {stats['monthly_totals'].get(as_of.strftime('%Y-%m'), 0):,}")]
    for x, label in footer:
        body += text(x, 281, label, "", 11)
    body += text(22, 298, "streaks within this window · today may still be in progress", "muted tiny")
    desc = f"{stats['total']} contributions. Current streak {stats['current_streak']} days; longest streak {stats['longest_streak']} days in the fetched window. As of {as_of}."
    return svg(860, 310, "filan214 contribution calendar", desc, body)


if __name__ == "__main__":
    run(lambda: save("contrib-heatmap.svg", render(read_json(DATA / "contributions.json"))))
