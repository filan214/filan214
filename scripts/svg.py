"""Self-contained, accessible SVG building blocks. Light is the fallback."""
import os
import re
from html import escape

from common import ROOT

THEME = '''
:root { color-scheme: light dark; --bg:#ffffff; --panel:#f6f8fa; --ink:#24292f; --muted:#59636e; --line:#d1d9e0; --accent:#16733c; --cyan:#0969da; --amber:#8a5700; --portrait:#353b43; --track:#e5e9ee; --p0:#ebedf0; --p1:#c6e8cb; --p2:#9bd7a4; --p3:#58b96b; --p4:#2a9345; --p5:#167036; }
@media (prefers-color-scheme: dark) {
 :root { --bg:#0d1117; --panel:#161b22; --ink:#e6edf3; --muted:#919ba7; --line:#30363d; --accent:#69f0a0; --cyan:#79c0ff; --amber:#e3b341; --portrait:#c9d1d9; --track:#21262d; --p0:#161b22; --p1:#0e4429; --p2:#006d32; --p3:#26a641; --p4:#39d353; --p5:#69f0a0; }
}
text { font-family:'Cascadia Code','SFMono-Regular',Consolas,'Liberation Mono',monospace; font-size:12px; fill:var(--ink); }
.bg {fill:var(--bg);stroke:var(--line)} .panel {fill:var(--panel)}
.ink {fill:var(--ink)} .muted {fill:var(--muted)} .accent {fill:var(--accent)} .cyan {fill:var(--cyan)} .amber {fill:var(--amber)} .portrait {fill:var(--portrait)}
.line {stroke:var(--line)} .track {fill:var(--track)} .small {font-size:10px} .tiny {font-size:9px} .large {font-size:22px;font-weight:600} .bold {font-weight:600}
.p0 {fill:var(--p0)} .p1 {fill:var(--p1)} .p2 {fill:var(--p2)} .p3 {fill:var(--p3)} .p4 {fill:var(--p4)} .p5 {fill:var(--p5)}
.unknown {fill:var(--bg);stroke:var(--line);stroke-dasharray:2 2}
'''
MOTION = '''
@keyframes enter {from {opacity:0;transform:translateY(7px)} to {opacity:1;transform:translateY(0)}}
@keyframes drop {from {opacity:0;transform:translateY(-12px)} to {opacity:1;transform:translateY(0)}}
.enter {animation:enter .55s ease-out both}
.drop {animation:drop .35s ease-out both}
'''
REDUCED = '''
@media (prefers-reduced-motion: reduce) {
 * {animation:none !important} .wipe {clip-path:none !important}
 .tag-cycle {display:none} .tag-static {display:inline}
}
'''


def clean(value):
    return "".join(c for c in str(value) if ord(c) >= 32 or c in "\n\t")


def esc(value):
    return escape(clean(value), quote=True)


def text(x, y, value, cls="", size=None, extra=""):
    size_attr = f' font-size="{size}"' if size else ""
    # Inline font-size overrides the text rule, but colors always live in <style>.
    if size:
        size_attr = f' style="font-size:{size}px"'
    return f'<text x="{x}" y="{y}" class="{cls}"{size_attr} {extra}>{esc(value)}</text>'


def rect(x, y, width, height, cls="panel", radius=4, extra=""):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" class="{cls}" {extra}/>'


def chrome(width, height, command, label="filan214 / ~"):
    return (rect(.5, .5, width-1, height-1, "bg", 12)
            + text(22, 27, "$", "accent bold") + text(38, 27, command, "muted small")
            + text(width-22, 27, label, "muted tiny", extra='text-anchor="end"')
            + f'<path d="M20 42H{width-20}" class="line"/>')


def wipe(identifier, x, y, width, height, content, delay=0, duration=.8):
    total = delay + duration
    times = f"0;{delay/total:.5f};1" if delay else "0;1"
    values = f"0;0;{width}" if delay else f"0;{width}"
    # Base geometry is the completed frame if SMIL is unsupported or STATIC=1.
    return (f'<defs><clipPath id="{identifier}" clipPathUnits="userSpaceOnUse">'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}">'
            f'<animate attributeName="width" values="{values}" keyTimes="{times}" begin="0s" dur="{total:.3f}s" repeatCount="1" fill="freeze"/>'
            f'</rect></clipPath></defs><g class="wipe" clip-path="url(#{identifier})">{content}</g>')


def svg(width, height, title, desc, body, css="", styles=""):
    static = os.environ.get("STATIC") == "1"
    if static:
        body = re.sub(r'<animate(?:Transform)?\b[^>]*/>', '', body)
        animation = '.tag-cycle{display:none}.tag-static{display:inline} *{animation:none!important}'
    else:
        animation = MOTION + css + REDUCED
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{esc(title)}</title>\n<desc id="desc">{esc(desc)}</desc>\n'
            f'<style>{THEME}{styles}{animation}</style>\n{body}\n</svg>\n')


def save(name, content):
    path = ROOT / name
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Rendered {path.name}")


def shorten(value, limit):
    value = " ".join(clean(value).split())
    return value if len(value) <= limit else value[:limit-1] + "…"
