#!/usr/bin/env python3
"""Generate deterministic ColdBrew raster branding from an owner-supplied image."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
IMAGES = ROOT / "docs" / "images"
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def contain(source: Image.Image, size: tuple[int, int], color: str) -> Image.Image:
    result = Image.new("RGB", size, color)
    fitted = ImageOps.contain(source.convert("RGB"), size, Image.Resampling.LANCZOS)
    result.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return result


def rounded_brand(source: Image.Image, size: int) -> Image.Image:
    border = max(3, size // 28)
    inner_size = size - border * 2
    portrait = ImageOps.fit(source.convert("RGB"), (inner_size, inner_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), "#0B1012")
    canvas.paste(portrait.convert("RGBA"), (border, border))
    mask = Image.new("L", (size, size), 0)
    mask_draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(mask)
    mask_draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 7, fill=255)
    canvas.putalpha(mask)
    draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(canvas)
    draw.rounded_rectangle(
        (border // 2, border // 2, size - border // 2 - 1, size - border // 2 - 1),
        radius=size // 7,
        outline="#80F0BC",
        width=border,
    )
    return canvas


def make_hero(source: Image.Image) -> Image.Image:
    width, height = 1600, 720
    canvas = Image.new("RGB", (width, height), "#0B1012")
    portrait = ImageOps.fit(
        source.convert("RGB"),
        (720, height),
        Image.Resampling.LANCZOS,
        centering=(0.58, 0.5),
    )
    portrait = ImageEnhance.Contrast(portrait).enhance(1.10)
    portrait = ImageEnhance.Brightness(portrait).enhance(0.82)
    canvas.paste(portrait, (880, 0))

    draw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(canvas, "RGBA")
    draw.rectangle((0, 0, 10, height), fill="#80F0BC")
    draw.rectangle((870, 0, 880, height), fill="#80F0BC")
    draw.rectangle((0, height - 94, width, height), fill=(8, 17, 13, 238))
    for x in (80, 360, 640, 820):
        draw.rectangle((x, 54, x + 2, 116), fill=(128, 240, 188, 130))
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

    avatar = rounded_brand(source, 512)
    avatar_path = IMAGES / "ishii-coldbrew-avatar.png"
    avatar.save(avatar_path, format="PNG", optimize=False, compress_level=9)

    gui_brand = rounded_brand(source, 62)
    gui_path = ASSETS / "ishii-brand.png"
    gui_brand.save(gui_path, format="PNG", optimize=False, compress_level=9)

    icon_path = ASSETS / "coldbrew-codex.ico"
    icon = rounded_brand(source, 256)
    icon.save(icon_path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    hero_path = IMAGES / "codex-brain-hero.png"
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
    parser.add_argument("source", type=Path, help="Owner-supplied square portrait")
    args = parser.parse_args()
    for path in generate(args.source.expanduser().resolve()):
        print(f"{path.relative_to(ROOT).as_posix()}  {sha256(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
