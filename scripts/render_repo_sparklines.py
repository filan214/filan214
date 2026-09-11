"""Small EKG-style lines drawn from real daily commit counts, not decorative pulses."""
from common import DATA, read_json, run
from svg import rect, save, svg, text, wipe


def render(project, fetched_at):
    width, height = 180, 52
    body = rect(.5, .5, width-1, height-1, "bg", 6)
    days = project.get("activity_days", []) if project else []
    if not days:
        body += text(10, 30, "History unavailable", "muted", 10)
        return svg(width, height, "Repository commit history", "No repository history available. Synced " + fetched_at, body)
    counts = [day["count"] for day in days]
    if any(type(count) is not int or count < 0 for count in counts):
        raise ValueError("Daily commit counts must be nonnegative integers")
    total, peak = sum(counts), max(counts)
    points = [(round(10 + 160*i/max(1, len(counts)-1), 2), round(29 - 22*count/max(1, peak), 2)) for i, count in enumerate(counts)]
    coordinates = " ".join(f"{x},{y}" for x, y in points)
    body += '<path d="M10 29H170" class="line spark-baseline"/>'
    trace = f'<polygon points="10,29 {coordinates} 170,29" class="spark-area"/>'
    trace += f'<polyline points="{coordinates}" class="spark-line"/>'
    trace += f'<circle cx="{points[-1][0]}" cy="{points[-1][1]}" r="2" class="accent"/>'
    body += wipe("history-reveal", 7, 4, 166, 30, trace, duration=1.1)
    body += text(10, 44, f"{total} commits", "muted", 8.5)
    body += text(170, 44, f"peak {peak}/d", "muted", 8.5, extra='text-anchor="end"')
    styles = '.spark-line{fill:none;stroke:var(--accent);stroke-width:1.6;stroke-linejoin:round;stroke-linecap:round}.spark-area{fill:var(--accent);opacity:.09}.spark-baseline{stroke-dasharray:2 3}'
    desc = (f"{project['name']}: {total} commits, {days[0]['date']} through {days[-1]['date']}, "
            f"default branch {project['default_branch']}, all authors, Asia/Jakarta. Peak {peak} commits per day. "
            f"Each line is scaled to its own peak. Synced {fetched_at}. Daily counts: " + ", ".join(str(count) for count in counts))
    return svg(width, height, project["name"] + " commit sparkline", desc, body, styles=styles)


def outputs(data):
    # Stable slots avoid abandoned per-repository files when the project list changes.
    projects = data["projects"]
    return {f"repo-activity-{i+1}.svg": render(projects[i] if i < len(projects) else None, data["fetched_at"]) for i in range(4)}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs(read_json(DATA / "builds.json")).items()])
