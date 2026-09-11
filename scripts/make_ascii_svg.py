"""Convert an existing grayscale/reference photo into a 100 x 53 ASCII grid."""
import argparse
from pathlib import Path

from common import ROOT, run
from svg import chrome, save, svg, text, wipe

RAMP = " .`:-=+*cs#%@"
COLS, ROWS = 100, 53


def ascii_rows(path):
    from PIL import Image, ImageOps
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert("L")
        # Respect the photo aspect ratio after accounting for tall character cells.
        ratio = source.width / source.height * (6 / 3.3)
        width = min(COLS, round(ROWS * ratio))
        height = min(ROWS, round(COLS / ratio))
        source = source.resize((max(1, width), max(1, height)), Image.Resampling.LANCZOS)
        canvas = Image.new("L", (COLS, ROWS), 255)
        canvas.paste(source, ((COLS-width)//2, (ROWS-height)//2))
        pixels = canvas.tobytes()
    return ["".join(RAMP[round((255-pixels[y*COLS+x])*(len(RAMP)-1)/255)] for x in range(COLS)) for y in range(ROWS)]


def render(path):
    rows = ascii_rows(path)
    body = chrome(370, 420, "cat portrait.txt", "100 × 53")
    for i, row in enumerate(rows):
        y = 63 + i*6
        line = text(20, y, row, "portrait", 5.5, extra='xml:space="preserve" textLength="330" lengthAdjust="spacingAndGlyphs"')
        body += wipe(f"row-{i}", 19, y-6, 332, 7, line, delay=i*.023, duration=.55)
    body += text(22, 399, "filan214", "muted tiny")
    body += text(348, 399, "portrait / ascii", "muted tiny", extra='text-anchor="end"')
    return svg(370, 420, "ASCII portrait of filan214", "Monochrome portrait made from 100 columns and 53 rows of text. Rows reveal left to right, top to bottom, once.", body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", nargs="?", type=Path, default=ROOT / "assets" / "portrait-gray.png")
    args = parser.parse_args()
    if not args.photo.exists():
        raise ValueError(f"Photo not found: {args.photo}. Pass a reference JPEG or first run prep_photo.py with your source photo.")
    save("filan-ascii.svg", render(args.photo))


if __name__ == "__main__":
    run(main)
