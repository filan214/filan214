"""Render hand-maintained thesis objectives; never scrape personal status."""
from common import DATA, read_json, run
from svg import rect, save, shorten, svg, text, wipe


def validate_status(status):
    done, total = status["objectives_done"], status["objectives_total"]
    defense = status["defense_status"]
    if type(done) is not int or type(total) is not int or total <= 0 or not 0 <= done <= total:
        raise ValueError("Objectives must be integers with 0 <= done <= total and total > 0")
    if not isinstance(defense, str) or not defense.strip() or len(defense) > 80:
        raise ValueError("defense_status must be a nonempty string of at most 80 characters")
    return done, total, " ".join(defense.split())


def render(status):
    done, total, defense = validate_status(status)
    label = f"{done}/{total} objectives finalized, defense: {defense}"
    percentage = done / total * 100
    body = rect(.5, .5, 859, 81, "bg", 12)
    body += text(22, 29, "$ thesis --progress", "accent small")
    body += text(838, 29, f"{percentage:.0f}% objectives", "muted small", extra='text-anchor="end"')
    body += rect(22, 46, 230, 8, "track")
    if done:
        width = round(230 * done / total, 2)
        body += wipe("progress", 22, 44, width, 12, rect(22, 46, width, 8, "accent"), duration=1.2)
    body += text(273, 55, shorten(label, 82), "", 10.5)
    return svg(860, 82, "Thesis objective progress", label, body)


def main():
    save("thesis-progress.svg", render(read_json(DATA / "status.json")))


if __name__ == "__main__":
    run(main)
