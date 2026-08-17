# -*- coding: utf-8 -*-
"""ColdBrew brand art: banner + og image + four project cards.
Rendered with matplotlib, using system fonts (msyh / consola)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib import patches
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

# --- fonts ---
YAHEI = fm.FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
YAHEI_BOLD = fm.FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")
CONSOLA = fm.FontProperties(fname=r"C:\Windows\Fonts\consola.ttf")
CONSOLA_BOLD = fm.FontProperties(fname=r"C:\Windows\Fonts\consolab.ttf")

# --- palette (matches the hub panel) ---
BG_TOP = np.array([0x0b, 0x0f, 0x14]) / 255
BG_BOTTOM = np.array([0x10, 0x15, 0x1b]) / 255
GRID = "#1a232e"
CYAN = "#9fd8ff"
MINT = "#8ff0a1"
SAND = "#f4e3c8"
COFFEE = "#6f4e37"
COFFEE_DARK = "#3a2a20"
ICE = "#a8d8e8"
DIM = "#5c6b7a"


def gradient_bg(ax, w, h, seed=7):
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h).reshape(-1, 1, 1)  # (h,1,1)
    base = BG_TOP[None, None, :] * (1 - y) + BG_BOTTOM[None, None, :] * y  # (h,1,3)
    base = np.repeat(base, w, axis=1)  # (h,w,3)
    noise = rng.normal(0, 0.006, (h, w, 1))
    img = np.clip(base + noise, 0, 1)
    ax.imshow(img, extent=[0, w, 0, h], aspect="auto", zorder=0)
    # subtle grid
    for gx in range(0, w + 1, 60):
        ax.plot([gx, gx], [0, h], color=GRID, lw=0.6, zorder=1, alpha=0.55)
    for gy in range(0, h + 1, 60):
        ax.plot([0, w], [gy, gy], color=GRID, lw=0.6, zorder=1, alpha=0.55)


def glow(text_obj, color, alpha=0.5):
    from matplotlib.patheffects import withStroke
    text_obj.set_path_effects([withStroke(linewidth=9, foreground=color, alpha=alpha)])


def iced_coffee(ax, cx, cy, scale=1.0):
    """Geometric iced americano: tall glass, ice cubes, straw, coaster."""
    s = scale
    # coaster shadow
    ax.add_patch(patches.Ellipse((cx, cy - 78 * s), 150 * s, 26 * s,
                                 facecolor="#00000055", zorder=2))
    # glass body (trapezoid)
    glass = [
        (cx - 62 * s, cy - 70 * s),
        (cx + 62 * s, cy - 70 * s),
        (cx + 48 * s, cy + 62 * s),
        (cx - 48 * s, cy + 62 * s),
    ]
    ax.add_patch(patches.Polygon(glass, closed=True, facecolor="#cfe8f0cc",
                                 edgecolor="#7fb4c8", lw=2 * s, zorder=3))
    # coffee level
    level = [
        (cx - 58 * s, cy - 18 * s),
        (cx + 58 * s, cy - 18 * s),
        (cx + 46 * s, cy + 56 * s),
        (cx - 46 * s, cy + 56 * s),
    ]
    ax.add_patch(patches.Polygon(level, closed=True, facecolor=COFFEE, alpha=0.92, zorder=4))
    # ice cubes above coffee
    cubes = [
        (cx - 30 * s, cy + 12 * s, 26 * s, 20),
        (cx + 8 * s, cy + 6 * s, 30 * s, 32),
        (cx - 6 * s, cy + 30 * s, 24 * s, 4),
        (cx + 30 * s, cy + 26 * s, 20 * s, 80),
    ]
    for ix, iy, iw, rot in cubes:
        ax.add_patch(patches.Rectangle((ix, iy), iw, iw * 0.9, angle=rot,
                                       facecolor=ICE, edgecolor="#6fa3b8",
                                       lw=1.6 * s, alpha=0.9, zorder=5))
    # straw
    ax.plot([cx + 34 * s, cx + 66 * s], [cy - 40 * s, cy - 86 * s],
            color=SAND, lw=5 * s, zorder=6, solid_capstyle="round")
    # bubbles
    rng = np.random.default_rng(11)
    for _ in range(9):
        bx = cx + rng.uniform(-34, 34) * s
        by = cy + rng.uniform(-48, 34) * s
        ax.add_patch(patches.Circle((bx, by), rng.uniform(1.6, 4.2) * s,
                                    facecolor="#ffffff88", zorder=7))
    # steam curls
    for k, dx in enumerate((-10, 4, 16)):
        xs = [cx + dx * s, cx + dx * s, cx + (dx + 6) * s]
        ys = [cy + 74 * s, cy + 96 * s, cy + 112 * s]
        ax.plot(xs, ys, color="#ffffff30", lw=3.5 * s, zorder=2,
                solid_capstyle="round")


def chip(ax, x, y, text, color, fontsize=15):
    ax.text(x, y, text, color=color, fontproperties=YAHEI_BOLD,
            fontsize=fontsize, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.55", facecolor="#141d26",
                      edgecolor=color, lw=1.4, alpha=0.95), zorder=8)


# ================= banner =================
W, H = 1200, 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
gradient_bg(ax, W, H)

# terminal decoration top-left
ax.text(70, H - 52, "● 冷咖啡终端 · ColdBrew Terminal", color=DIM,
        fontproperties=YAHEI, fontsize=15, va="center")
for k, c in enumerate(("#ff6b6b", "#ffd166", MINT)):
    ax.add_patch(patches.Circle((34 + k * 26, H - 52), 6, color=c, zorder=8))

# brand wordmark
t = ax.text(70, 402, "冷咖啡", color=SAND, fontproperties=YAHEI_BOLD, fontsize=120, zorder=8)
glow(t, SAND, 0.25)
t = ax.text(352, 402, "ColdBrew", color=CYAN, fontproperties=CONSOLA_BOLD, fontsize=72, zorder=8)
glow(t, CYAN, 0.25)
ax.text(72, 320, "四合一破甲 正式版", color="#e8eef5", fontproperties=YAHEI, fontsize=40, zorder=8)
ax.text(72, 258, "GPT-5.6 · Claude · Grok 4.6 · DeepSeek v4 Pro", color=MINT,
        fontproperties=CONSOLA, fontsize=26, zorder=8)
ax.text(72, 204, "一键部署 / 一键启动 / 一键恢复 / 一键打包发布", color=DIM,
        fontproperties=YAHEI, fontsize=19, zorder=8)

# QQ chips bottom-left
chip(ax, 140, 96, "QQ 群 1057540028", CYAN, 17)
chip(ax, 412, 96, "QQ 群 1077074552", MINT, 17)

# coffee on the right
iced_coffee(ax, 950, 330, scale=1.25)

# fake code lines bottom-right
for k in range(4):
    y = 66 - k * 26
    ax.add_patch(patches.Rectangle((640, y), 120 + k * 60, 10,
                                   facecolor=[CYAN, MINT, SAND, DIM][k], alpha=0.28, zorder=8))

fig.savefig(OUT / "banner.png", dpi=100, facecolor=BG_TOP)
plt.close(fig)
print("banner.png done")

# ================= og / social preview =================
W, H = 1200, 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
gradient_bg(ax, W, H, seed=21)

iced_coffee(ax, 600, 300, scale=1.05)
t = ax.text(600, 480, "冷咖啡 ColdBrew", color=SAND, fontproperties=YAHEI_BOLD,
            fontsize=92, ha="center", zorder=9)
glow(t, SAND, 0.3)
ax.text(600, 396, "四合一破甲 · 正式版", color=CYAN, fontproperties=YAHEI_BOLD,
        fontsize=44, ha="center", zorder=9)
ax.text(600, 334, "GPT-5.6  ·  Claude  ·  Grok 4.6  ·  DeepSeek v4 Pro", color=MINT,
        fontproperties=CONSOLA, fontsize=26, ha="center", zorder=9)
ax.text(600, 150, "github.com/3641397194-wq", color=DIM, fontproperties=CONSOLA,
        fontsize=20, ha="center", zorder=9)

fig.savefig(OUT / "og-image.png", dpi=100, facecolor=BG_TOP)
plt.close(fig)
print("og-image.png done")

# ================= project cards =================
CARDS = [
    ("GPT-5.6", "codex-coldbrew", "eni-solo v4.0.0 · 89 技能\n石井人格 · 确定性路由", CYAN, "CARD-GPT"),
    ("Claude Code", "claude-coldbrew", "多层规则部署 · 破甲 Studio\n冷咖啡激活契约", SAND, "CARD-CLAUDE"),
    ("Grok 4.6", "grok4.6-coldbrew", "会话模板 · 系统提示词部署\n可逆会话工程", MINT, "CARD-GROK"),
    ("DeepSeek v4 Pro", "deepseek-harness", "Harness 配置 · 深海控制台\n可逆提示词部署", "#b39ddb", "CARD-DEEPSEEK"),
]
for name, slug, desc, color, _ in CARDS:
    W, H = 640, 320
    fig = plt.figure(figsize=(6.4, 3.2), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    gradient_bg(ax, W, H, seed=len(name))
    ax.add_patch(patches.Rectangle((0, H - 8), W, 8, facecolor=color, zorder=9))
    ax.text(46, 210, name, color=color, fontproperties=YAHEI_BOLD, fontsize=54, zorder=8)
    ax.text(46, 132, desc, color="#c9d4de", fontproperties=YAHEI, fontsize=21,
            linespacing=1.7, zorder=8)
    ax.text(46, 58, "冷咖啡 ColdBrew · 四合一破甲", color=DIM, fontproperties=YAHEI,
            fontsize=15, zorder=8)
    ax.text(W - 46, 58, slug, color=DIM, fontproperties=CONSOLA, fontsize=14,
            ha="right", zorder=8)
    fig.savefig(OUT / f"card-{slug}.png", dpi=100, facecolor=BG_TOP)
    plt.close(fig)
    print(f"card-{slug}.png done")

print("ALL ART DONE ->", OUT)
