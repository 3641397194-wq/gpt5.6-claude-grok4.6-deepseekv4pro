from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# =========================
# 基础配置
# =========================

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "docs" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_MONO_BOLD = r"C:\Windows\Fonts\consolab.ttf"

BG_TOP = "#0b0f14"
BG_BOTTOM = "#10151b"
GRID = "#1a232e"
SAND = "#f4e3c8"
ICE = "#dff4ff"
MINT = "#9ff2c5"
WHITE = "#f5f7fa"
MUTED = "#82909e"


# =========================
# 字体与文字工具
# =========================

def font(path, size):
    return ImageFont.truetype(path, size)


def fit_text(draw, text, fnt, max_width, min_size=10, path=FONT_REGULAR):
    size = fnt.size
    while size > min_size:
        box = draw.textbbox((0, 0), text, font=fnt)
        if box[2] - box[0] <= max_width:
            return fnt
        size -= 1
        fnt = font(path, size)
    return fnt


def text_size(draw, text, fnt, stroke_width=0):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke_width)
    return box[2] - box[0], box[3] - box[1]


def draw_text_safe(draw, xy, text, fnt, fill, max_width=None,
                   anchor=None, stroke_width=0, stroke_fill=None):
    x, y = xy
    if max_width is not None:
        fnt = fit_text(draw, text, fnt, max_width, path=fnt.path if hasattr(fnt, "path") else FONT_REGULAR)
    box = draw.textbbox(
        (x, y), text, font=fnt, anchor=anchor,
        stroke_width=stroke_width
    )
    if box[0] < 0:
        x += -box[0]
    if box[1] < 0:
        y += -box[1]
    draw.text(
        (x, y), text, font=fnt, fill=fill, anchor=anchor,
        stroke_width=stroke_width, stroke_fill=stroke_fill
    )
    return fnt


def draw_centered(draw, xy, text, fnt, fill, max_width=None,
                  stroke_width=0, stroke_fill=None):
    if max_width is not None:
        fnt = fit_text(draw, text, fnt, max_width)
    draw.text(
        xy, text, font=fnt, fill=fill, anchor="mm",
        stroke_width=stroke_width, stroke_fill=stroke_fill
    )
    return fnt


# =========================
# 背景、网格与装饰
# =========================

def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient_background(width, height, top=BG_TOP, bottom=BG_BOTTOM):
    c1 = np.array(hex_rgb(top), dtype=np.float32)
    c2 = np.array(hex_rgb(bottom), dtype=np.float32)

    yy, xx = np.mgrid[0:height, 0:width]
    t = (xx / max(1, width - 1) * 0.58 + yy / max(1, height - 1) * 0.42)
    t = np.clip(t, 0.0, 1.0)[..., None]

    arr = np.clip(c1 * (1.0 - t) + c2 * t, 0, 255).astype(np.uint8)

    # 右上角微光晕
    gx, gy = width * 0.84, height * 0.08
    dist = np.sqrt(((xx - gx) / width) ** 2 + ((yy - gy) / height) ** 2)
    glow = np.clip(1.0 - dist / 0.42, 0, 1)[..., None]
    glow_color = np.array([43, 91, 118], dtype=np.float32)
    arr = np.clip(arr.astype(np.float32) + glow * glow_color * 0.18, 0, 255)

    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def add_grid(image, spacing=24, color=GRID, alpha=110):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    width, height = image.size
    rgb = hex_rgb(color)

    for x in range(0, width + spacing, spacing):
        draw.line((x, 0, x, height), fill=(*rgb, alpha), width=1)
    for y in range(0, height + spacing, spacing):
        draw.line((0, y, width, y), fill=(*rgb, alpha), width=1)

    return Image.alpha_composite(image, layer)


def add_corner_marks(draw, width, height, color, alpha=180):
    c = (*hex_rgb(color), alpha)
    draw.line((22, height - 28, 88, height - 28), fill=c, width=1)
    draw.line((22, height - 28, 22, height - 12), fill=c, width=1)
    draw.line((width - 88, 28, width - 22, 28), fill=c, width=1)
    draw.line((width - 22, 28, width - 22, 44), fill=c, width=1)


def rounded_box(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def capsule(draw, xy, label, color, fnt, padding_x=14, padding_y=8):
    x1, y1, x2, y2 = xy
    rounded_box(
        draw, xy, radius=(y2 - y1) // 2,
        fill=(255, 255, 255, 8),
        outline=(*hex_rgb(color), 220),
        width=1
    )
    draw.text(
        ((x1 + x2) // 2, (y1 + y2) // 2),
        label, font=fnt, fill=color, anchor="mm"
    )


def terminal_dots(draw, x, y):
    draw.ellipse((x, y, x + 10, y + 10), fill="#ff6b6b")
    draw.ellipse((x + 17, y, x + 27, y + 10), fill="#ffd166")
    draw.ellipse((x + 34, y, x + 44, y + 10), fill="#8ff0a1")


def code_lines(draw, x, y, colors):
    lines = [
        ("$ brew --mode cold", 94),
        ("> bypass.layer(4)", 112),
        (":: ready", 66),
    ]
    for i, (txt, length) in enumerate(lines):
        yy = y + i * 14
        draw.text((x, yy), txt, font=font(FONT_MONO_BOLD, 10),
                  fill=colors[i % len(colors)])
        draw.line(
            (x + 120, yy + 6, x + 120 + length, yy + 6),
            fill=(*hex_rgb(colors[i % len(colors)]), 90),
            width=1
        )


# =========================
# 冰美式几何插画
# =========================

def draw_coffee_illustration(image, center_x, base_y, scale=1.0, compact=False):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def sc(v):
        return int(v * scale)

    cx = center_x
    top = base_y - sc(245)
    cup_w = sc(190)
    cup_h = sc(230)
    left = cx - cup_w // 2
    right = cx + cup_w // 2
    bottom = top + cup_h

    # 杯垫投影
    draw.ellipse(
        (cx - sc(126), base_y - sc(20), cx + sc(126), base_y + sc(22)),
        fill=(0, 0, 0, 105)
    )
    draw.ellipse(
        (cx - sc(105), base_y - sc(14), cx + sc(105), base_y + sc(12)),
        fill=(29, 43, 51, 220),
        outline=(100, 151, 166, 120),
        width=max(1, sc(2))
    )

    # 吸管
    straw_start = (cx + sc(26), top + sc(38))
    straw_end = (cx + sc(91), top - sc(82))
    draw.line(
        (straw_start[0], straw_start[1], straw_end[0], straw_end[1]),
        fill="#9fd8ff", width=max(2, sc(5))
    )
    draw.line(
        (straw_start[0] + sc(5), straw_start[1],
         straw_end[0] + sc(5), straw_end[1]),
        fill=(255, 255, 255, 90), width=max(1, sc(1))
    )

    # 杯身
    glass_fill = (161, 219, 235, 34)
    draw.polygon(
        [
            (left, top + sc(20)),
            (right, top + sc(20)),
            (right - sc(24), bottom - sc(18)),
            (cx + sc(14), bottom),
            (cx - sc(14), bottom),
            (left + sc(24), bottom - sc(18)),
        ],
        fill=glass_fill,
        outline=(185, 235, 245, 205)
    )

    # 咖啡液体
    coffee_top = top + sc(86)
    draw.polygon(
        [
            (left + sc(18), coffee_top),
            (right - sc(18), coffee_top),
            (right - sc(39), bottom - sc(29)),
            (cx + sc(11), bottom - sc(9)),
            (cx - sc(11), bottom - sc(9)),
            (left + sc(39), bottom - sc(29)),
        ],
        fill=(75, 44, 30, 220)
    )
    draw.ellipse(
        (left + sc(18), coffee_top - sc(11),
         right - sc(18), coffee_top + sc(17)),
        fill=(112, 68, 42, 230),
        outline=(244, 193, 135, 160),
        width=max(1, sc(2))
    )

    # 冰块
    ice_color = (211, 244, 250, 160)
    ice_edge = (242, 255, 255, 210)
    cubes = [
        [
            (cx - sc(62), coffee_top - sc(6)),
            (cx - sc(20), coffee_top - sc(18)),
            (cx - sc(8), coffee_top + sc(24)),
            (cx - sc(49), coffee_top + sc(34)),
        ],
        [
            (cx + sc(12), coffee_top - sc(5)),
            (cx + sc(54), coffee_top - sc(18)),
            (cx + sc(68), coffee_top + sc(24)),
            (cx + sc(28), coffee_top + sc(32)),
        ],
        [
            (cx - sc(8), coffee_top + sc(28)),
            (cx + sc(28), coffee_top + sc(18)),
            (cx + sc(42), coffee_top + sc(58)),
            (cx + sc(2), coffee_top + sc(68)),
        ],
    ]
    for cube in cubes:
        draw.polygon(cube, fill=ice_color, outline=ice_edge)
        draw.line((cube[0], cube[2]), fill=(255, 255, 255, 90), width=max(1, sc(1)))

    # 气泡
    bubbles = [
        (left + sc(48), top + sc(62), 4),
        (left + sc(78), top + sc(48), 3),
        (right - sc(49), top + sc(67), 5),
        (right - sc(77), top + sc(48), 3),
        (cx + sc(64), top + sc(112), 3),
    ]
    for bx, by, br in bubbles:
        draw.ellipse(
            (bx - sc(br), by - sc(br), bx + sc(br), by + sc(br)),
            outline=(187, 236, 248, 180), width=max(1, sc(1))
        )

    # 杯口高光
    draw.arc(
        (left - sc(3), top + sc(8), right + sc(3), top + sc(42)),
        180, 360, fill=(236, 252, 255, 210), width=max(1, sc(2))
    )
    draw.line(
        (left + sc(26), top + sc(30), left + sc(42), bottom - sc(49)),
        fill=(255, 255, 255, 90), width=max(1, sc(2))
    )

    return Image.alpha_composite(image, layer)


# =========================
# Banner
# =========================

def render_banner():
    width, height = 1200, 630
    image = gradient_background(width, height)
    image = add_grid(image, spacing=26, alpha=105)
    draw = ImageDraw.Draw(image)

    terminal_dots(draw, 54, 48)
    draw.text((112, 42), "冷咖啡终端", font=font(FONT_REGULAR, 18), fill=MINT)
    draw.text((112, 68), "COLDBREW / SYSTEM CONSOLE", font=font(FONT_MONO_BOLD, 10), fill=MUTED)

    draw_text_safe(
        draw, (58, 145), "冷咖啡",
        font(FONT_BOLD, 130), SAND, max_width=545
    )
    draw.text((575, 166), "ColdBrew", font=font(FONT_MONO_BOLD, 38), fill="#9fd8ff")
    draw.line((575, 216, 825, 216), fill=(159, 216, 255, 110), width=1)

    draw.text(
        (62, 296), "四合一破甲 · 正式版",
        font=font(FONT_BOLD, 38), fill=WHITE
    )
    draw.text(
        (65, 353), "ONE BREW. FOUR MINDS. ZERO NOISE.",
        font=font(FONT_MONO_BOLD, 13), fill=MUTED
    )

    labels = [
        ("GPT-5.6", "#9fd8ff"),
        ("Claude", "#f4e3c8"),
        ("Grok 4.6", "#8ff0a1"),
        ("DeepSeek v4 Pro", "#b39ddb"),
    ]
    x = 62
    y = 408
    for label, color in labels:
        fnt = font(FONT_MONO_BOLD, 15)
        tw, th = text_size(draw, label, fnt)
        w = tw + 28
        capsule(draw, (x, y, x + w, y + 34), label, color, fnt)
        x += w + 10

    draw.text(
        (62, 574), "QQ 群 1057540028 · 1077074552",
        font=font(FONT_REGULAR, 15), fill=MINT
    )
    code_lines(draw, 925, 540, ["#9fd8ff", "#f4e3c8", "#8ff0a1"])

    draw_coffee_illustration(image, 1000, 490, scale=0.82)
    draw.ellipse((867, 87, 874, 94), fill="#9fd8ff")
    draw.ellipse((887, 112, 892, 117), fill="#8ff0a1")
    draw.ellipse((1080, 83, 1086, 89), fill="#b39ddb")

    image.convert("RGB").save(OUT_DIR / "banner.png", "PNG", optimize=True)


# =========================
# OG 社交卡
# =========================

def render_og():
    width, height = 1200, 630
    image = gradient_background(width, height)
    image = add_grid(image, spacing=30, alpha=95)
    draw = ImageDraw.Draw(image)

    terminal_dots(draw, 56, 48)
    draw.text(
        (600, 61), "COLD BREW · 四合一破甲",
        font=font(FONT_MONO_BOLD, 18), fill=MINT, anchor="mm"
    )

    draw.text(
        (600, 220), "冷咖啡",
        font=font(FONT_BOLD, 92), fill=SAND, anchor="rm"
    )
    draw.text(
        (610, 220), "ColdBrew",
        font=font(FONT_MONO_BOLD, 54), fill="#9fd8ff", anchor="lm"
    )

    models = "GPT-5.6     Claude     Grok 4.6     DeepSeek v4 Pro"
    draw.text(
        (600, 314), models,
        font=font(FONT_MONO_BOLD, 23), fill=WHITE, anchor="mm"
    )
    draw.line((318, 351, 882, 351), fill=(159, 216, 255, 90), width=1)

    for x, color in [(370, "#9fd8ff"), (530, "#f4e3c8"), (670, "#8ff0a1"), (830, "#b39ddb")]:
        draw_coffee_illustration(image, x, 500, scale=0.26)

    draw.text(
        (600, 591), "COFFEE FOR EVERY MODEL",
        font=font(FONT_MONO_BOLD, 14), fill=MUTED, anchor="mm"
    )

    add_corner_marks(draw, width, height, "#9fd8ff")
    image.convert("RGB").save(OUT_DIR / "og-image.png", "PNG", optimize=True)


# =========================
# 模型卡片
# =========================

def render_card(filename, model, tagline, color, code, model_size=48):
    width, height = 640, 320
    image = gradient_background(width, height, "#090d12", "#121a21")
    image = add_grid(image, spacing=24, alpha=105)
    draw = ImageDraw.Draw(image)

    rgb = hex_rgb(color)
    draw.rectangle((0, 0, width, 8), fill=rgb)

    draw.text(
        (30, 28), "冷咖啡 ColdBrew",
        font=font(FONT_MONO_BOLD, 14), fill=rgb
    )
    draw.text(
        (width - 30, 28), "MODEL CARD / 04",
        font=font(FONT_MONO_BOLD, 11), fill=MUTED, anchor="ra"
    )

    draw.line((30, 63, width - 30, 63), fill=(*rgb, 105), width=1)

    model_font = fit_text(
        draw, model, font(FONT_BOLD, model_size), 520,
        min_size=28, path=FONT_BOLD
    )
    draw.text((32, 101), model, font=model_font, fill=WHITE)

    draw.rounded_rectangle(
        (32, 177, 48, 193), radius=8,
        fill=rgb
    )
    draw.text(
        (62, 172), tagline,
        font=font(FONT_REGULAR, 20), fill=SAND
    )

    draw.text(
        (width - 30, height - 34), code,
        font=font(FONT_MONO_BOLD, 13), fill=rgb, anchor="ra"
    )

    draw.arc(
        (width - 142, height - 146, width - 42, height - 46),
        190, 350, fill=(*rgb, 130), width=2
    )
    draw.arc(
        (width - 122, height - 126, width - 62, height - 66),
        10, 170, fill=(*rgb, 95), width=1
    )
    draw.ellipse(
        (width - 91, height - 101, width - 83, height - 93),
        fill=rgb
    )

    draw.line((31, 255, 190, 255), fill=(*rgb, 75), width=1)
    draw.line((31, 263, 135, 263), fill=(*rgb, 55), width=1)
    draw.line((31, 271, 92, 271), fill=(*rgb, 40), width=1)

    image.convert("RGB").save(OUT_DIR / filename, "PNG", optimize=True)


# =========================
# 主渲染流程
# =========================

def main():
    render_banner()
    render_og()

    render_card(
        "card-codex-coldbrew.png",
        "GPT-5.6",
        "eni-solo v4.0.0 · 89 技能 · 石井人格",
        "#9fd8ff",
        "CB / CODEX-01",
        model_size=58
    )
    render_card(
        "card-claude-coldbrew.png",
        "Claude Code",
        "多层规则部署 · 破甲 Studio",
        "#f4e3c8",
        "CB / CLAUDE-02",
        model_size=48
    )
    render_card(
        "card-grok4.6-coldbrew.png",
        "Grok 4.6",
        "会话模板 · 系统提示词部署",
        "#8ff0a1",
        "CB / GROK-03",
        model_size=55
    )
    render_card(
        "card-deepseek-harness.png",
        "DeepSeek v4 Pro",
        "Harness 配置 · 深海控制台",
        "#b39ddb",
        "CB / DEEP-04",
        model_size=43
    )


if __name__ == "__main__":
    main()

