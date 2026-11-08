"""Repository cards styled after GitHub's profile list. One image per card, so each can link."""
import textwrap

from common import DATA, read_json, run
from svg import rect, save, shorten, svg, text

SHOWN = 6
WIDTH, HEIGHT = 420, 120
# GitHub's API names a repository's language but not the color Linguist assigns it.
LANGUAGE_COLORS = {"C": "#555555", "C#": "#178600", "C++": "#f34b7d", "CSS": "#663399", "Dart": "#00B4AB", "Go": "#00ADD8",
                   "HTML": "#e34c26", "Java": "#b07219", "JavaScript": "#f1e05a", "Jupyter Notebook": "#DA5B0B", "Kotlin": "#A97BFF",
                   "PHP": "#4F5D95", "Python": "#3572A5", "R": "#198CE7", "Ruby": "#701516", "Rust": "#dea584", "Shell": "#89e051",
                   "Swift": "#F05138", "TypeScript": "#3178c6", "Vue": "#41b883"}
STYLES = '''
.sans{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif}
.pill{fill:none;stroke:var(--line)}
'''


def card(repo):
    language, description = repo["language"], repo["description"]
    body = rect(.5, .5, WIDTH-1, HEIGHT-1, "bg", 6)
    body += text(16, 31, shorten(repo["name"], 38), "cyan bold sans", 14)
    body += rect(WIDTH-65, 15, 49, 21, "pill", 10.5)
    body += text(WIDTH-40.5, 29, "Public", "muted sans", 11, extra='text-anchor="middle"')
    for i, line in enumerate(textwrap.wrap(shorten(description, 130), width=64)[:2]):
        body += text(16, 58+i*18, line, "muted sans", 12)
    if language:
        body += '<circle cx="22" cy="99" r="6" class="lang"/>'
        body += text(34, 103, shorten(language, 40), "muted sans", 12)
    dot = f".lang{{fill:{LANGUAGE_COLORS.get(language, 'var(--muted)')}}}"
    desc = " ".join(part for part in (description, f"Primary language: {language}." if language else "") if part) or "Public repository."
    return svg(WIDTH, HEIGHT, repo["name"], desc, body, styles=STYLES + dot)


def outputs(data):
    return {f"repo-card-{i+1}.svg": card(repo) for i, repo in enumerate(data["repositories"][:SHOWN])}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs(read_json(DATA / "builds.json")).items()])
