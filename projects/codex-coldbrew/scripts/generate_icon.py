#!/usr/bin/env python3
"""Regenerate the original Codex ColdBrew multi-size Windows icon."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "coldbrew-codex.ico"
CANVAS = 1024


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def render() -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), "#10231e")
    draw = ImageDraw.Draw(image)
    rounded(draw, (56, 56, 968, 968), 204, "#f3f0e8")
    rounded(draw, (94, 94, 930, 930), 172, "#15332a")

    # Coffee cup silhouette and a Codex-style execution chevron share one mark.
    rounded(draw, (230, 386, 664, 690), 72, "#f4f1e8")
    draw.rounded_rectangle((618, 438, 806, 620), radius=82, width=44, outline="#f4f1e8")
    draw.rounded_rectangle((294, 704, 716, 756), radius=26, fill="#f0b35a")
    draw.line((344, 330, 414, 250, 484, 330), fill="#f0b35a", width=34, joint="curve")
    draw.line((514, 330, 584, 250, 654, 330), fill="#f0b35a", width=34, joint="curve")
    draw.polygon(((285, 535), (382, 470), (382, 516), (464, 516), (464, 554), (382, 554), (382, 600)), fill="#15332a")
    draw.polygon(((536, 516), (618, 516), (618, 470), (715, 535), (618, 600), (618, 554), (536, 554)), fill="#15332a")
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    image = render()
    image.save(output, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
