"""Scrolling push heads with a full readable log in the adjacent README disclosure."""
import os
from datetime import datetime

from common import DATA, JAKARTA, read_json, run
from render_build_spotlight import sync_label
from svg import chrome, esc, rect, save, shorten, svg, text


def render(data):
    pushes = data["pushes"][:10]
    static = os.environ.get("STATIC") == "1"
    visible = max(1, len(pushes)) if static else min(3, max(1, len(pushes)))
    row_height, top = 34, 81
    window_height = visible * row_height
    height = top + window_height + 53
    body = chrome(860, height, "git log --oneline --all", "CROSS-REPO PUSH STREAM")
    body += text(22, 64, f"{len(pushes)} available public pushes · newest first · all branches", "muted", 10)
    body += text(838, 64, "one head commit / push", "muted tiny", extra='text-anchor="end"')
    body += f'<defs><clipPath id="stream-window">{rect(20, top, 820, window_height, radius=0)}</clipPath></defs>'
    rows = pushes if static or len(pushes) < 2 else pushes + pushes[:visible]
    content = ''
    for i, item in enumerate(rows):
        y = top + 20 + i*row_height
        when = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).astimezone(JAKARTA).strftime("%m-%d %H:%M")
        # Preserve repository identity and the exact message in the SVG description.
        content += text(24, y, when, "muted", 9)
        content += text(99, y, item["sha"][:7], "accent bold", 10.5)
        content += text(159, y, shorten(item["repo"].split('/', 1)[-1], 27), "cyan", 10.5)
        content += text(342, y, shorten(item["message"], 77), "", 10.5)
        content += f'<path d="M22 {y+11}H838" class="line stream-divider"/>'
    if not pushes:
        content = text(24, top+22, "No eligible public pushes in GitHub's available event window.", "muted", 11)
    body += f'<g clip-path="url(#stream-window)"><g class="stream-scroll">{content}</g></g>'
    css = ''
    if len(pushes) > 1:
        distance = len(pushes)*row_height
        css = (f'@keyframes stream-scroll{{from{{transform:translateY(0)}}to{{transform:translateY(-{distance}px)}}}}'
               f'.stream-scroll{{animation:stream-scroll {len(pushes)*4}s linear infinite}}')
    body += text(22, height-29, "Public event feed may lag · push dates in WIB · full linked log below ↓", "muted", 9)
    body += text(838, height-12, "synced " + sync_label(data), "muted tiny", extra='text-anchor="end"')
    desc = (f"{len(pushes)} latest available public pushes across repositories and branches; one head commit per push. "
            f"Fetched {data['fetched_at']}. GitHub's public event window is limited and may be delayed. "
            + (" | ".join(f"{item['created_at']} {item['repo']} {item['branch']} {item['sha']} {item['message']}" for item in pushes) if pushes else "No eligible public pushes available."))
    return svg(860, height, "Cross-repository commit stream", desc, body, css, styles='.stream-divider{opacity:.45}')


if __name__ == "__main__":
    run(lambda: save("commit-stream.svg", render(read_json(DATA / "commit-stream.json"))))
