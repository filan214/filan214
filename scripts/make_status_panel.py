"""htop-inspired mock processes for real ventures; these are not telemetry."""
from common import run
from svg import chrome, rect, save, svg, text

PROCESSES = [
    ("214", "thesis.py", "[running]", "89%", "SARIMA / Streamlit DSS", "accent"),
    ("215", "freelance-dev", "[running]", "—", "web + mobile development", "accent"),
    ("216", "jogja-ride", "[cron: weekends]", "—", "Jogja Ride Premium", "amber"),
]


def render():
    body = chrome(860, 229, "htop --user filan214", "ventures / 03")
    body += text(22, 66, "3 processes · 2 running · 1 scheduled", "muted small")
    body += text(838, 66, "mock activity / real ventures", "muted tiny", extra='text-anchor="end"')
    body += rect(20, 79, 820, 26, "panel", 4)
    for x, label in ((30, "PID"), (90, "PROCESS"), (300, "STATE"), (476, "ACTIVITY"), (592, "CONTEXT")):
        body += text(x, 96, label, "muted tiny bold")
    for i, (pid, name, state, activity, detail, color) in enumerate(PROCESSES):
        y = 127 + i*32
        content = text(30, y, pid, "muted small") + text(90, y, name, "bold")
        content += text(300, y, state, color, 11) + text(476, y, activity, "", 11)
        content += text(592, y, detail, "muted", 11)
        body += f'<g class="enter" style="animation-delay:{i*.14:.2f}s">{content}</g>'
    body += text(22, 213, "F1 learn   F2 build   F3 iterate", "muted tiny")
    body += text(838, 213, "objective completion tracked below ↓", "muted tiny", extra='text-anchor="end"')
    return svg(860, 229, "Current ventures", "Mock htop activity: thesis.py running at 89%; freelance-dev running; jogja-ride scheduled on weekends. These activity values are illustrative, not measured thesis completion.", body)


if __name__ == "__main__":
    run(lambda: save("status-panel.svg", render()))
