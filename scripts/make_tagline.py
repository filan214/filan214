"""The one intentionally looping animation: four CSS typewriter phrases."""
from common import run
from svg import rect, save, svg, text

PHRASES = ["IS student", "thesis researcher", "freelance dev", "weekend driver"]


def render():
    body = rect(.5, .5, 859, 49, "bg", 10)
    body += text(22, 30, "$ whoami", "accent", 11)
    css = ".tag-static{display:none}.tag-word{clip-path:inset(0 100% 0 0);transform-box:fill-box}"
    for i, phrase in enumerate(PHRASES):
        start, typed, held, erased = i*25, i*25+7, i*25+19, (i+1)*25-1
        css += (f"@keyframes type{i} {{0%,{start}% {{clip-path:inset(0 100% 0 0)}}"
                f"{typed}%,{held}% {{clip-path:inset(0 0 0 0)}}"
                f"{erased}%,100% {{clip-path:inset(0 100% 0 0)}}}}"
                f".word{i} {{animation:type{i} 16s steps({len(phrase)},end) infinite}}")
        body += f'<g class="tag-cycle">{text(115, 30, phrase + "_", f"tag-word word{i}", 12)}</g>'
    body += text(115, 30, " / ".join(PHRASES), "tag-static", 11)
    body += text(838, 30, "Yogyakarta, ID", "muted small", extra='text-anchor="end"')
    return svg(860, 50, "The many hats of filan214", "; ".join(PHRASES), body, css)


if __name__ == "__main__":
    run(lambda: save("tagline.svg", render()))
