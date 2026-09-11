"""Optional source photo pipeline: rembg -> CLAHE -> white -> grayscale."""
import argparse
from pathlib import Path

from common import ROOT, run


def prepare(source, output):
    # Heavy dependencies are imported only when explicitly preparing a photo.
    import cv2
    import numpy as np
    from PIL import Image, ImageOps
    from rembg import remove

    with Image.open(source) as photo:
        rgba = remove(ImageOps.exif_transpose(photo).convert("RGBA")).convert("RGBA")
    pixels = np.asarray(rgba)
    lab = cv2.cvtColor(pixels[:, :, :3], cv2.COLOR_RGB2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    enhanced = Image.fromarray(np.dstack((rgb, pixels[:, :, 3])))
    white = Image.new("RGBA", enhanced.size, (255, 255, 255, 255))
    gray = Image.alpha_composite(white, enhanced).convert("L")
    output.parent.mkdir(parents=True, exist_ok=True)
    gray.save(output)
    print(f"Prepared {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source photo supplied by you")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "portrait-gray.png")
    args = parser.parse_args()
    if not args.source.is_file():
        raise ValueError(f"Source photo not found: {args.source}")
    if args.source.resolve() == args.output.resolve():
        raise ValueError("Choose a separate output file to preserve the original source photo")
    prepare(args.source, args.output)


if __name__ == "__main__":
    run(main)
