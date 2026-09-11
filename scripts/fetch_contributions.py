"""Fetch the public GitHub calendar without a token; preserve exact counts."""
import re
from collections import defaultdict
from datetime import date, timedelta

from bs4 import BeautifulSoup

from common import DATA, USERNAME, GitHub, run, today, write_json


def parse_contributions(html):
    soup = BeautifulSoup(html, "html.parser")
    tips = {tip.get("for"): tip.get_text(" ", strip=True) for tip in soup.select("tool-tip[for]")}
    days = {}
    for cell in soup.select("[data-date]"):
        day = date.fromisoformat(cell["data-date"]).isoformat()
        raw = cell.get("data-count")
        if raw is not None:
            count = int(raw.replace(",", ""))
        else:
            label = tips.get(cell.get("id"), cell.get("aria-label", ""))
            match = re.search(r"\b(No|[\d,]+) contributions?\b", label, re.I)
            if not match:
                raise ValueError(f"No exact contribution count for {day}; GitHub markup may have changed")
            count = 0 if match[1].lower() == "no" else int(match[1].replace(",", ""))
        level = int(cell.get("data-level", 0 if count == 0 else 1))
        if count < 0 or level not in range(5):
            raise ValueError(f"Invalid calendar value for {day}")
        days[day] = {"date": day, "count": count, "level": level}
    if not days:
        raise ValueError("No contribution calendar found; refusing to replace real data with zeros")
    return [days[key] for key in sorted(days)]


def contribution_stats(days, as_of):
    counts = {date.fromisoformat(d["date"]): d["count"] for d in days if date.fromisoformat(d["date"]) <= as_of}
    monthly = defaultdict(int)
    longest = streak = 0
    previous = None
    for day, count in sorted(counts.items()):
        monthly[day.strftime("%Y-%m")] += count
        streak = (streak + 1 if previous == day - timedelta(days=1) else 1) if count > 0 else 0
        longest = max(longest, streak)
        previous = day
    cursor = as_of if counts.get(as_of, 0) > 0 else as_of - timedelta(days=1)
    current = 0
    while as_of in counts and counts.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    best = max(sorted(counts), key=counts.get) if counts and max(counts.values()) > 0 else None
    return {"total": sum(counts.values()), "current_streak": current, "longest_streak": longest,
            "best_day": {"date": best.isoformat(), "count": counts[best]} if best else None,
            "monthly_totals": dict(sorted(monthly.items()))}


def main():
    as_of = today()
    url = f"https://github.com/users/{USERNAME}/contributions"
    start = as_of - timedelta(days=(as_of.weekday() + 1) % 7, weeks=52)
    client = GitHub()
    combined = {}
    # This endpoint selects a single calendar year when given `to`, even if
    # `from` belongs to the prior year. Fetch every intersecting year explicitly.
    for year in range(start.year, as_of.year + 1):
        end = min(as_of, date(year, 12, 31))
        html = client.get(url, params={"to": end.isoformat()}, headers={"Accept": "text/html"}).text
        for day in parse_contributions(html):
            if start.isoformat() <= day["date"] <= as_of.isoformat():
                combined[day["date"]] = day
    days = [combined[key] for key in sorted(combined)]
    if not days or days[-1]["date"] < (as_of - timedelta(days=1)).isoformat():
        raise ValueError("Contribution calendar is stale; existing snapshot was preserved")
    write_json(DATA / "contributions.json", {"username": USERNAME, "as_of": as_of.isoformat(), "source": url, "days": days, "stats": contribution_stats(days, as_of)})
    print(f"Fetched {len(days)} contribution days")


if __name__ == "__main__":
    run(main)
