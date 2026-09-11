"""The one intentionally looping animation: four CSS typewriter phrases."""
from common import DATA, read_json, run
from svg import rect, save, shorten, svg, text


def render(data=None, languages=None):
    data = data if data is not None else read_json(DATA / "builds.json")
    languages = languages if languages is not None else read_json(DATA / "languages.json")
    project = data["projects"][0] if data["projects"] else None
    phrases = [f"{data['profile']['public_repos']} public repositories",
               "latest: " + (shorten(project["name"], 44) if project else "no project yet"),
               "code: " + (", ".join(item["name"] for item in languages["languages"][:3]) or "no language data"),
               f"{data['eligible_repo_count']} projects in the showcase pool"]
    body = rect(.5, .5, 859, 49, "bg", 10)
    body += text(22, 30, "$ now", "accent", 11)
    css = ".tag-static{display:none}.tag-word{clip-path:inset(0 100% 0 0);transform-box:fill-box}"
    for i, phrase in enumerate(phrases):
        start, typed, held, erased = i*25, i*25+7, i*25+19, (i+1)*25-1
        css += (f"@keyframes type{i} {{0%,{start}% {{clip-path:inset(0 100% 0 0)}}"
                f"{typed}%,{held}% {{clip-path:inset(0 0 0 0)}}"
                f"{erased}%,100% {{clip-path:inset(0 100% 0 0)}}}}"
                f".word{i} {{animation:type{i} 16s steps({len(phrase)},end) infinite}}")
        body += f'<g class="tag-cycle">{text(115, 30, phrase + "_", f"tag-word word{i}", 12)}</g>'
    body += text(115, 30, shorten(phrases[1] + " · " + phrases[0], 88), "tag-static", 10)
    body += text(838, 30, "from GitHub", "muted small", extra='text-anchor="end"')
    return svg(860, 50, "Current public projects", "; ".join(phrases) + "; synced " + data["fetched_at"], body, css)


if __name__ == "__main__":
    run(lambda: save("tagline.svg", render()))
