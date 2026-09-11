"""One terminal line, revealed once and frozen; full message in description."""
from common import DATA, read_json, run
from svg import rect, save, shorten, svg, text, wipe


def render(data):
    event = data.get("event")
    if event:
        line = f"{event['sha'][:7]}  {event['repo']}  {event['message']}"
        desc = f"Latest available public push on {event['created_at']}: {line}"
    else:
        line = "No public push in the available event window."
        desc = line
    body = rect(.5, .5, 859, 49, "bg", 10)
    body += text(20, 30, "$ git log --oneline -1", "accent", 10.5)
    content = text(178, 30, shorten(line, 98), "", 10.5)
    # Fixed-step SMIL gives a character-by-character terminal reveal.
    revealed = wipe("commit-line", 178, 10, 662, 30, content, duration=1.8)
    steps = 98
    values = ";".join(str(round(662*i/steps, 2)) for i in range(steps+1))
    times = ";".join(str(round(i/steps, 6)) for i in range(steps+1))
    import re
    revealed = re.sub(r'values="[^"]+" keyTimes="[^"]+"', f'values="{values}" keyTimes="{times}" calcMode="discrete"', revealed)
    body += revealed
    return svg(860, 50, "Latest public commit", desc, body)


if __name__ == "__main__":
    run(lambda: save("commit-log.svg", render(read_json(DATA / "last-event.json"))))
