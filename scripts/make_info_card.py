"""Neofetch biography; use STATIC=1 for a completed preview frame."""
import textwrap

from common import run
from svg import chrome, rect, save, svg, text

ROWS = [
    ("Now", "Final-semester Information Systems student, UAJY"),
    ("Focus", "Data Analytics → Data Science / AI Engineering"),
    ("Building", "Freelance web/mobile dev, Jogja Ride Premium"),
    ("Stack", "Python, SQL, Next.js, Tailwind, Drizzle ORM, PostgreSQL, Power BI"),
    ("Highlight", "Thesis — SARIMA 0.83% MAPE vs RF 2.95% / LSTM 4.62%, Streamlit DSS dashboard"),
]


def render():
    body = chrome(490, 420, "neofetch", "profile / 02")
    body += text(22, 78, "filan214", "accent bold", 21)
    body += text(134, 78, "@ yogyakarta", "muted", 13)
    body += text(22, 99, "information systems · data · things that work", "muted small")
    y = 132
    for index, (key, value) in enumerate(ROWS):
        content = text(22, y, key.lower(), "cyan bold", 11)
        lines = textwrap.wrap(value, width=49, break_long_words=False)
        for line in lines:
            content += text(105, y, line, "", 11.5)
            y += 18
        body += f'<g class="enter" style="animation-delay:{index*.13:.2f}s">{content}</g>'
        y += 13
    for index, color in enumerate(("ink", "muted", "cyan", "accent", "amber", "p3")):
        body += rect(22 + index*22, 381, 16, 9, color, 2)
    body += text(468, 391, "always learning_", "muted tiny", extra='text-anchor="end"')
    return svg(490, 420, "About filan214", "; ".join(f"{key}: {value}" for key, value in ROWS), body)


if __name__ == "__main__":
    run(lambda: save("info-card.svg", render()))
