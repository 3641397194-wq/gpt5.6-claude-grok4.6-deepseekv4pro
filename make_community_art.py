from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)
ASSET = ROOT / "projects" / "grok4.6-coldbrew" / "docs" / "images"

def font(size: int, bold: bool = False):
    candidates = [
        Path(r"C:\\Windows\\Fonts\\segoeuib.ttf" if bold else r"C:\\Windows\\Fonts\\segoeui.ttf"),
        Path(r"C:\\Windows\\Fonts\\arialbd.ttf" if bold else r"C:\\Windows\\Fonts\\arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()

def make_qr(text: str, path: Path) -> None:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    qr.make_image(fill_color="#0b1020", back_color="white").convert("RGB").save(path)

def qq_card(source: Path, target: Path, title: str, group: str, accent: str) -> None:
    src = Image.open(source).convert("RGB")
    crop = src.crop((86, 108, 208, 226))
    crop = ImageEnhance.Contrast(crop).enhance(1.08).filter(ImageFilter.SHARPEN)
    canvas = Image.new("RGB", (720, 820), "#f5f8fc")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((18, 18, 701, 801), radius=38, fill="white", outline="#dbe5ef", width=3)
    draw.rounded_rectangle((18, 18, 701, 142), radius=38, fill="#0d1b2a")
    draw.rectangle((18, 105, 701, 142), fill="#0d1b2a")
    draw.rounded_rectangle((44, 46, 116, 114), radius=18, fill=accent)
    draw.text((80, 80), "QQ", font=font(23, True), fill="#07111b", anchor="mm")
    draw.text((142, 47), title, font=font(31, True), fill="#ffffff")
    draw.text((142, 91), "Group ID  " + group, font=font(22), fill="#a9c3d1")
    qr = ImageOps.contain(crop, (470, 610), method=Image.Resampling.LANCZOS)
    qr_canvas = Image.new("RGB", (500, 640), "white")
    qr_canvas.paste(qr, ((500 - qr.width) // 2, (640 - qr.height) // 2))
    qr_canvas = ImageOps.expand(qr_canvas, border=10, fill="#edf3f8")
    canvas.paste(qr_canvas, ((720 - qr_canvas.width) // 2, 170))
    ImageDraw.Draw(canvas).text((360, 768), "Scan to join - follow the live QQ prompt", font=font(20), fill="#5f7280", anchor="mm")
    canvas.save(target)

def draw_qr_card(draw, board, box, title, subtitle, qr_path, accent, link=None):
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x+w, y+h), radius=30, fill="#ffffff", outline="#d5e4ee", width=3)
    draw.rounded_rectangle((x, y, x+w, y+104), radius=30, fill="#0d1b2a")
    draw.rectangle((x, y+70, x+w, y+104), fill="#0d1b2a")
    draw.rounded_rectangle((x+26, y+28, x+78, y+80), radius=14, fill=accent)
    draw.text((x+52, y+54), "QR", font=font(16, True), fill="#07111b", anchor="mm")
    draw.text((x+100, y+28), title, font=font(25, True), fill="#ffffff")
    draw.text((x+100, y+64), subtitle, font=font(18), fill="#b9d0db")
    src = Image.open(qr_path).convert("RGB")
    if src.height / src.width > 1.3:
        src = ImageOps.fit(src, (190, 230), method=Image.Resampling.LANCZOS, centering=(0.5, 0.52))
    else:
        src = ImageOps.contain(src, (230, 230), method=Image.Resampling.LANCZOS)
    frame = Image.new("RGB", (270, 270), "white")
    frame.paste(src, ((330-src.width)//2, (350-src.height)//2))
    frame = ImageOps.expand(frame, border=8, fill="#e8f1f6")
    board.paste(frame, (x+(w-frame.width)//2, y+128))
    if link:
        ImageDraw.Draw(board).text((x+28, y+h-36), link, font=font(18), fill="#527282")

def draw_info_card(draw, box):
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x+w, y+h), radius=30, fill="#ffffff", outline="#d5e4ee", width=3)
    draw.rounded_rectangle((x, y, x+w, y+104), radius=30, fill="#0d1b2a")
    draw.rectangle((x, y+70, x+w, y+104), fill="#0d1b2a")
    draw.rounded_rectangle((x+26, y+28, x+78, y+80), radius=14, fill="#80f0bc")
    draw.text((x+52, y+54), "INFO", font=font(13, True), fill="#07111b", anchor="mm")
    draw.text((x+100, y+28), "Community links", font=font(25, True), fill="#ffffff")
    draw.text((x+100, y+64), "Keep this page bookmarked", font=font(18), fill="#b9d0db")
    lines = [
        "QQ groups: 1057540028 / 1077074552",
        "Telegram group: t.me/chachachacha99999",
        "Telegram channel: t.me/chachacha99999999",
        "WeChat QR validity follows the live image",
    ]
    yy = y + 152
    for index, line in enumerate(lines):
        color = "#263f52" if index < 3 else "#617b8b"
        draw.ellipse((x+34, yy+7, x+46, yy+19), fill="#80f0bc" if index < 3 else "#ffd68a")
        draw.text((x+64, yy), line, font=font(19), fill=color)
        yy += 54

def main():
    make_qr("https://t.me/chachachacha99999", OUT / "telegram-group-v2.png")
    # Exact channel URL supplied by the user.
    make_qr("https://t.me/chachacha99999999", OUT / "telegram-channel-v2.png")
    qq_card(ASSET / "qq-group-1.png", OUT / "qq-group-1-v2.png", "ColdBrew QQ", "1057540028", "#80f0bc")
    qq_card(ASSET / "qq-group-2.png", OUT / "qq-group-2-v2.png", "Codex / Claude", "1077074552", "#9aa7ff")

    width, height = 1600, 1720
    board = Image.new("RGB", (width, height), "#f5f8fc")
    draw = ImageDraw.Draw(board)
    draw.rectangle((0, 0, width, 230), fill="#0d1b2a")
    draw.ellipse((1260, -240, 1730, 220), fill="#18394b")
    draw.ellipse((-160, 120, 280, 520), fill="#122d3d")
    draw.text((92, 58), "ColdBrew Community", font=font(54, True), fill="#f7e8c7")
    draw.text((96, 130), "Four-model workbench / community hub", font=font(30), fill="#90dceb")
    draw.text((96, 178), "QQ groups  |  WeChat group  |  Telegram group  |  Telegram channel", font=font(20), fill="#b8c8d2")
    draw_qr_card(draw, board, (80, 280, 690, 420), "QQ Group 1057540028", "ColdBrew QQ", OUT / "qq-group-1-v2.png", "#80f0bc", "QQ group 1057540028")
    draw_qr_card(draw, board, (830, 280, 690, 420), "QQ Group 1077074552", "Codex / Claude", OUT / "qq-group-2-v2.png", "#9aa7ff", "QQ group 1077074552")
    draw_qr_card(draw, board, (80, 750, 690, 420), "WeChat Group", "Scan and note: ColdBrew", ASSET / "wechat-group.png", "#ffd68a", "QR validity follows the image")
    draw_qr_card(draw, board, (830, 750, 690, 420), "Telegram Group", "Discussion and support", OUT / "telegram-group-v2.png", "#66d9ff", "t.me/chachachacha99999")
    draw_info_card(draw, (80, 1220, 690, 330))
    draw_qr_card(draw, board, (830, 1220, 690, 420), "Telegram Channel", "Announcements and releases", OUT / "telegram-channel-v2.png", "#9aa7ff", "t.me/chachacha99999999")
    draw.rounded_rectangle((80, 1650, 1520, 1695), radius=18, fill="#dbeaf2")
    draw.text((800, 1672), "github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro", font=font(17), fill="#456674", anchor="mm")
    board.save(OUT / "community-board-v2.png")

if __name__ == "__main__":
    main()
