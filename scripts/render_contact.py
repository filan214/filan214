"""Contact cards. README images cannot hold two links, so each channel is its own SVG."""
from common import run
from svg import esc, rect, save, svg, text, wipe

EMAIL = "valentinus.filan@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/valentinus-filan-gunawan-087538226"
WIDTH, HEIGHT = 420, 110

STYLES = '''
:root{--brand:#0a66c2;--mail-wash:#e8f6ee}
@media(prefers-color-scheme:dark){:root{--brand:#4d9de0;--mail-wash:#11251c}}
.brand{fill:var(--brand)} .mail-wash{fill:var(--mail-wash)}
.mark{fill:#ffffff;font-family:Arial,Helvetica,sans-serif;font-weight:700}
.on-fill{fill:var(--bg);font-weight:700}
.stroke{fill:none;stroke:var(--accent);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.body{fill:var(--mail-wash);stroke:var(--accent);stroke-width:2;stroke-linejoin:round}
.letter{fill:var(--bg);stroke:var(--accent);stroke-width:1.5}
.ink-line{stroke:var(--muted);stroke-width:1.5;stroke-linecap:round}
.ring{fill:none;stroke:var(--brand);stroke-width:2;opacity:0}
.letter,.ring{transform-box:fill-box;transform-origin:center}
'''
# Keyframes are dropped for STATIC=1 and reduced motion, leaving the finished frame.
MOTION = '''
@keyframes rise{from{transform:translateY(10px)} to{transform:translateY(0)}}
@keyframes pulse{from{opacity:.7;transform:scale(1)} to{opacity:0;transform:scale(1.35)}}
@keyframes blink{50%{opacity:0}}
.letter{animation:rise .7s ease-out .5s both}
.ring{animation:pulse 1.4s ease-out .4s 2}
.cursor{animation:blink 1.1s steps(1) 1.6s infinite}
'''


def envelope(x, y):
    # Letter first, then the envelope body hides its lower half, then the flap.
    letter = (rect(x+19, y+12, 22, 18, "letter", 2)
              + f'<path d="M{x+23} {y+18}h14M{x+23} {y+23}h9" class="ink-line"/>')
    return (rect(x, y, 60, 60, "mail-wash", 14)
            + f'<g class="letter">{letter}</g>'
            + rect(x+15, y+21, 30, 21, "body", 3)
            + f'<path d="M{x+15} {y+22}L{x+30} {y+33}L{x+45} {y+22}" class="stroke"/>')


def linkedin(x, y):
    return (rect(x, y, 60, 60, "ring", 14) + rect(x, y, 60, 60, "brand", 14)
            + text(x+13, y+42, "in", "mark", 30))


def card(slug, label, command, handle, note, action, icon, accent, description):
    body = f'<g class="enter">{rect(.5, .5, WIDTH-1, HEIGHT-1, "bg", 12)}'
    body += rect(0, 18, 3, HEIGHT-36, accent, 1)
    body += icon
    body += text(100, 44, "$", "accent bold", 11) + text(112, 44, command, "muted", 11)
    typed = (f'<text x="100" y="69" class="bold" style="font-size:13px">{esc(handle)}'
             f'<tspan class="cursor {accent}">▋</tspan></text>')
    body += wipe(f"type-{slug}", 98, 54, 226, 22, typed, delay=.3, duration=1.1)
    body += text(100, 92, note, "muted tiny")
    body += rect(330, 40, 74, 30, accent, 15)
    body += text(367, 60, action, "on-fill", 12, extra='text-anchor="middle"')
    body += '</g>'
    return svg(WIDTH, HEIGHT, f"{label} — Valentinus Filan", description, body, css=MOTION, styles=STYLES)


def outputs():
    return {"contact-email.svg": card("email", "Email", "mail --to", EMAIL, "Opens your mail app", "Write ↗",
                                      envelope(22, 25), "accent", f"Send an email to {EMAIL}."),
            "contact-linkedin.svg": card("linkedin", "LinkedIn", "open --linkedin", "in/valentinus-filan-gunawan",
                                         "Profile, projects & experience", "Connect ↗", linkedin(22, 25), "brand",
                                         "Open Valentinus Filan Gunawan's LinkedIn profile.")}


if __name__ == "__main__":
    run(lambda: [save(name, content) for name, content in outputs().items()])
