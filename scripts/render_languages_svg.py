"""Terminal bars for top languages, measured as public repository bytes."""
from common import DATA, read_json, run
from svg import chrome, rect, save, shorten, svg, text, wipe


def render(data):
    languages = data["languages"][:6]
    height = 113 + max(1, len(languages))*29
    body = chrome(860, height, "languages --bytes --top 6", "toolbox / 04")
    body += text(22, 65, f"{data['repo_count']} eligible public projects · {data['total_bytes']:,} bytes · default branches", "muted small")
    if not languages:
        body += text(22, 99, "No language bytes available in public repositories.", "muted")
    for i, language in enumerate(languages):
        y = 91 + i*29
        body += text(22, y+5, shorten(language["name"], 19), "cyan", 11)
        body += rect(178, y-5, 525, 10, "track", 3)
        width = round(525 * language["bytes"] / data["total_bytes"], 3)
        body += wipe(f"language-{i}", 178, y-6, width, 13, rect(178, y-5, width, 10, "accent" if i % 2 == 0 else "cyan", 3), delay=i*.1, duration=.9)
        body += text(838, y+4, f"{language['percent']:5.1f}%", "", 11, extra='text-anchor="end"')
    body += text(22, height-18, "share of code bytes, not proficiency · excludes forks, archives & configured repos", "muted tiny")
    body += text(838, height-18, f"{data['as_of']}", "muted tiny", extra='text-anchor="end"')
    desc = "Public repository language bytes: " + ", ".join(f"{v['name']} {v['percent']} percent" for v in languages)
    return svg(860, height, "Most-used public repository languages", desc, body)


if __name__ == "__main__":
    run(lambda: save("languages.svg", render(read_json(DATA / "languages.json"))))
