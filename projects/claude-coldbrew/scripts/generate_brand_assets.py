#!/usr/bin/env python3
"""Generate deterministic Claude ColdBrew branding from an owner image."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
from PIL import ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
IMAGES = ROOT / "docs" / "images"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rounded_brand(source: Image.Image, size: int) -> Image.Image:
    border = max(3, size // 28)
    inner = size - border * 2
    portrait = ImageOps.fit(source.convert("RGB"), (inner, inner), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), "#0B0E0D")
    canvas.paste(portrait.convert("RGBA"), (border, border))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 7, fill=255)
    canvas.putalpha(mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        (border // 2, border // 2, size - border // 2 - 1, size - border // 2 - 1),
        radius=size // 7,
        outline="#C9FF4A",
        width=border,
    )
    return canvas


def make_hero(source: Image.Image) -> Image.Image:
    width, height = 1600, 720
    canvas = Image.new("RGB", (width, height), "#0B0E0D")
    # Keep the copy-free left field for page HTML and reserve the hero bitmap for the brand portrait.
    portrait = ImageOps.fit(source.convert("RGB"), (680, height), Image.Resampling.LANCZOS, centering=(0.58, 0.5))
    portrait = ImageEnhance.Contrast(portrait).enhance(1.12)
    canvas.paste(portrait, (920, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rectangle((0, 0, 10, height), fill="#C9FF4A")
    draw.rectangle((908, 0, 920, height), fill="#C9FF4A")
    draw.rectangle((0, height - 72, 908, height), fill=(8, 15, 11, 235))
    for x in (80, 360, 640, 1420):
        draw.rectangle((x, 54, x + 2, 116), fill=(201, 255, 74, 130))
    return canvas


def convert_qr(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    image.thumbnail((268, 268), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (288, 288), "white")
    canvas.paste(image, ((288 - image.width) // 2, (288 - image.height) // 2))
    canvas.save(destination, format="PNG", optimize=False, compress_level=9)


def generate(source_path: Path) -> list[Path]:
    if source_path.is_symlink() or not source_path.is_file():
        raise RuntimeError(f"Owner image is missing or unsafe: {source_path}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")
    if source.width < 512 or source.height < 512:
        raise RuntimeError(f"Owner image is too small: {source.size}")
    source_copy = ASSETS / "ishii-brand-source.jpg"
    if source_path.resolve() != source_copy.resolve():
        source.save(source_copy, format="JPEG", quality=95, optimize=False, progressive=False)
    # Always derive every output from the canonical repository copy. This keeps
    # repeated runs byte-for-byte stable instead of recompressing the JPEG.
    with Image.open(source_copy) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")
    avatar_path = IMAGES / "ishii-coldbrew-avatar.png"
    rounded_brand(source, 512).save(avatar_path, format="PNG", optimize=False, compress_level=9)
    gui_path = ASSETS / "ishii-brand.png"
    rounded_brand(source, 62).save(gui_path, format="PNG", optimize=False, compress_level=9)
    icon_path = ASSETS / "coldbrew.ico"
    rounded_brand(source, 256).save(
        icon_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    hero_path = IMAGES / "claude-brain-hero.png"
    make_hero(source).save(hero_path, format="PNG", optimize=False, compress_level=9)

    qr_paths: list[Path] = []
    for name in ("qq-group-codex", "qq-group-codex-claude"):
        qr_source = IMAGES / f"{name}.jpg"
        qr_target = IMAGES / f"{name}.png"
        if not qr_source.is_file():
            raise RuntimeError(f"Community image is missing: {qr_source}")
        convert_qr(qr_source, qr_target)
        qr_paths.append(qr_target)
    return [source_copy, avatar_path, gui_path, icon_path, hero_path, *qr_paths]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    for path in generate(args.source.expanduser().resolve()):
        print(f"{path.relative_to(ROOT).as_posix()}  {sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
