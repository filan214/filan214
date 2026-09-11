"""An animated project spotlight, with real 28-day default-branch activity."""
import textwrap
from datetime import datetime

from common import DATA, JAKARTA, read_json, run
from svg import chrome, rect, save, shorten, svg, text, wipe


def sync_label(data):
    return datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00")).astimezone(JAKARTA).strftime("%d %b %Y · %H:%M WIB")


def render(data, languages):
    width, height = 860, 392
    body = chrome(width, height, "git portfolio --latest", "RECENT BUILD SPOTLIGHT")
    styles = '.activity-bar{transform-box:fill-box;transform-origin:bottom}.hero-title{font-weight:600}.outline{fill:none;stroke:var(--line)}'
    projects = data["projects"]
    if not projects:
        body += text(28, 115, "No eligible public projects to feature.", "muted")
        body += text(28, 148, "New public projects will appear after the next successful sync.", "muted small")
        return svg(width, height, "Recent Build Spotlight", "No eligible public projects. Synced " + data["fetched_at"], body, styles=styles)
    project = projects[0]
    days = data["activity_days"]
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    body += text(28, 72, "01 / MOST RECENTLY PUSHED", "accent bold", 10)
    title_lines = textwrap.wrap(shorten(project["title"], 65), width=32)[:2]
    for i, line in enumerate(title_lines):
        body += text(28, 108+i*27, line, "hero-title", 23)
    body += text(28, 170, shorten(project["full_name"], 58), "cyan", 11)
    description = project["description"] or "Open the repository to explore its README and code."
    for i, line in enumerate(textwrap.wrap(shorten(description, 148), width=62)[:3]):
        body += text(28, 193+i*17, line, "muted", 10.5)
    body += rect(28, 251, 464, 63, "panel", 8)
    for i, (value, label) in enumerate(((str(total), "commits / 28 days"), (str(active), "active days"), (str(project["stars"]), "stars"))):
        x = 43 + i*154
        body += text(x, 278, value, "accent bold", 22)
        body += text(x, 298, label, "muted tiny")
    body += rect(512, 61, 320, 253, "panel", 10)
    body += text(530, 85, "REPOSITORY ACTIVITY", "muted bold", 10)
    body += text(530, 106, shorten(project["default_branch"], 22) + " · all authors", "muted tiny")
    peak = max((day["count"] for day in days), default=0)
    body += text(814, 106, f"peak {peak}/day", "muted tiny", extra='text-anchor="end"')
    for i, day in enumerate(days):
        x, baseline = 530 + i*10, 181
        body += rect(x, baseline, 6, 2, "track", 1)
        if day["count"]:
            bar_height = round(60*day["count"]/max(1, peak), 2)
            body += f'<g class="enter" style="animation-delay:{i*.025:.3f}s">'
            body += rect(x, baseline-bar_height, 6, bar_height, "activity-bar accent", 2)
            body += '</g>'
    if days:
        body += text(530, 200, days[0]["date"][5:], "muted tiny")
        body += text(810, 200, days[-1]["date"][5:] + " WIB", "muted tiny", extra='text-anchor="end"')
    body += '<path d="M530 213H814" class="line"/>'
    body += text(530, 236, "DEFAULT BRANCH TIP", "muted tiny")
    commit = project["commit"]
    body += text(530, 257, commit["sha"][:7], "accent bold", 12)
    body += text(814, 257, commit["created_at"][:10], "muted tiny", extra='text-anchor="end"')
    for i, line in enumerate(textwrap.wrap(shorten(commit["message"], 75), width=40)[:2]):
        body += text(530, 276+i*16, line, "", 10)
    byte_values = languages.get("repos", {}).get(project["full_name"], {}).get("languages", {})
    ranked = sorted(((name, count) for name, count in byte_values.items() if count > 0), key=lambda row: (-row[1], row[0]))
    body += text(28, 339, "CODE MIX", "muted tiny")
    byte_total = sum(count for _, count in ranked)
    x = 110
    for i, (name, count) in enumerate(ranked):
        bar_width = 200*count/byte_total
        body += wipe(f"mix-{i}", x, 328, bar_width, 14, rect(x, 331, bar_width, 7, ("accent", "cyan", "amber", "muted")[i % 4], 0), delay=.2, duration=.8)
        x += bar_width
    mix = " · ".join(f"{name} {100*count/byte_total:.0f}%" for name, count in ranked[:3]) if ranked else "Language bytes unavailable"
    body += text(324, 339, shorten(mix, 76), "muted", 10)
    body += text(28, 373, "Explore code, commit & project history below ↓", "cyan", 10)
    body += text(832, 373, "synced " + sync_label(data), "muted tiny", extra='text-anchor="end"')
    desc = (f"{project['title']}. {project['full_name']}. {project['description']} "
            f"{total} commits across {active} active days in the last 28 calendar days, default branch, all authors. "
            f"Most recent repository push: {project['pushed_at']}. Default branch tip: {commit['sha']}: {commit['message']}. "
            f"Language bytes: {mix}. Snapshot fetched {data['fetched_at']}.")
    return svg(width, height, "Recent Build Spotlight — " + project["name"], desc, body, styles=styles)


if __name__ == "__main__":
    run(lambda: save("recent-build.svg", render(read_json(DATA / "builds.json"), read_json(DATA / "languages.json"))))
