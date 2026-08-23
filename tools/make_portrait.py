#!/usr/bin/env python3
"""Regenerate the baked ASCII portrait from a photo.

    pip install pillow
    python tools/make_portrait.py path/to/photo.jpg --width 44

Copy the printed block into the ART = r\"\"\"...\"\"\" constant in
../update_profile.py. Keeping ART baked means the main script stays
dependency-free (stdlib only), so the daily Action needs no pip install.

Tips for a dark-background, front-lit photo (like the current one):
  --invert  is ON by default (background -> empty, lit face -> drawn)
  raise --contrast / lower --gamma to make the face bolder.
"""
import argparse
from PIL import Image, ImageEnhance

RAMP = "@@%%##**++==--::..  "  # dark -> light (doubled for finer tonal steps)


def to_ascii(path, width, invert, contrast, gamma):
    img = ImageEnhance.Contrast(Image.open(path).convert("L")).enhance(contrast)
    w, h = img.size
    new_h = max(1, int((h / w) * width * 0.5))
    img = img.resize((width, new_h))
    px = [int(255 * ((p / 255) ** gamma)) for p in img.tobytes()]
    if invert:
        px = [255 - p for p in px]
    n = len(RAMP)
    lines = ["".join(RAMP[min(n - 1, p * n // 256)] for p in px[r * width:(r + 1) * width])
             for r in range(new_h)]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--width", type=int, default=44)
    ap.add_argument("--contrast", type=float, default=1.5)
    ap.add_argument("--gamma", type=float, default=0.85)
    ap.add_argument("--no-invert", dest="invert", action="store_false")
    a = ap.parse_args()
    print("\n".join(to_ascii(a.image, a.width, a.invert, a.contrast, a.gamma)))
