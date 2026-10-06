"""Static contact buttons. README images cannot hold two links, so each channel is its own SVG."""
from common import run
from svg import rect, save, svg, text

EMAIL = "valentinus.filan@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/valentinus-filan-gunawan-087538226"

STYLES = '''
:root{--brand:#0a66c2}
@media(prefers-color-scheme:dark){:root{--brand:#4d9de0}}
.brand{fill:var(--brand)} .mark{fill:#ffffff;font-family:Arial,Helvetica,sans-serif;font-weight:700}
.stroke{fill:none;stroke:var(--accent);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
'''


def envelope(x, y):
    return (rect(x, y, 28, 20, "stroke", 3)
            + f'<path d="M{x+2} {y+3}L{x+14} {y+12}L{x+26} {y+3}" class="stroke"/>')


def linkedin(x, y):
    return rect(x, y, 26, 26, "brand", 5) + text(x+4, y+21, "in", "mark", 17)


def button(label, handle, icon, description):
    body = rect(.5, .5, 299, 55, "bg", 10)
    body += icon
    body += text(62, 24, label, "bold", 13)
    body += text(62, 42, handle, "muted", 10)
    body += text(280, 33, "↗", "accent bold", 14, extra='text-anchor="end"')
    return svg(300, 56, label + " — Valentinus Filan", description, body, styles=STYLES)


def outputs():
    return {"contact-email.svg": button("Email", EMAIL, envelope(19, 18), f"Send an email to {EMAIL}."),
            "contact-linkedin.svg": button("LinkedIn", "in/valentinus-filan-gunawan", linkedin(20, 15),
                                           "Open Valentinus Filan Gunawan's LinkedIn profile.")}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs().items()])
