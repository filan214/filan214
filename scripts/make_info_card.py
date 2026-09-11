"""Neofetch panel sourced from the public GitHub profile and project snapshot."""
import textwrap

from common import DATA, read_json, run
from render_build_spotlight import sync_label
from svg import chrome, rect, save, shorten, svg, text

def render(data=None, languages=None):
    data = data if data is not None else read_json(DATA / "builds.json")
    languages = languages if languages is not None else read_json(DATA / "languages.json")
    profile, projects = data["profile"], data["projects"]
    recent = projects[0] if projects else None
    rows = [
        ("name", profile.get("name") or profile["login"]),
        ("public", f"{profile['public_repos']} repositories on GitHub"),
        ("social", f"{profile['followers']} followers / {profile['following']} following"),
        ("latest", recent["name"] if recent else "No eligible public project"),
        ("pushed", recent["pushed_at"][:10] if recent else "No push available"),
        ("code", ", ".join(item["name"] for item in languages["languages"][:4]) or "No language data"),
    ]
    body = chrome(490, 420, "neofetch --github", "PUBLIC PROFILE")
    body += text(22, 78, profile["login"], "accent bold", 23)
    body += text(22, 101, shorten(profile.get("bio") or "Public code · recent projects · actual activity", 60), "muted", 11)
    y = 139
    for index, (key, value) in enumerate(rows):
        content = text(22, y, key, "cyan bold", 11)
        for line in textwrap.wrap(shorten(value, 86), width=43)[:2]:
            content += text(105, y, line, "", 11.5)
            y += 18
        body += f'<g class="enter" style="animation-delay:{index*.13:.2f}s">{content}</g>'
        y += 13
    for index, color in enumerate(("ink", "muted", "cyan", "accent", "amber", "p3")):
        body += rect(22 + index*22, 365, 16, 9, color, 2)
    body += text(22, 399, "github.com/" + profile["login"], "muted tiny")
    body += text(468, 399, sync_label(data), "muted tiny", extra='text-anchor="end"')
    return svg(490, 420, "GitHub profile of " + profile["login"], "; ".join(f"{key}: {value}" for key, value in rows) + "; synced " + data["fetched_at"], body)


if __name__ == "__main__":
    run(lambda: save("info-card.svg", render()))
