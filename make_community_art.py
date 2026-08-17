from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def make_qr(text: str, path: Path) -> None:
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=3)
    code.add_data(text)
    code.make(fit=True)
    code.make_image(fill_color="#0b1020", back_color="white").convert("RGB").save(path)


def main() -> None:
    make_qr("https://t.me/chachachacha99999", OUT / "telegram-group.png")
    make_qr("https://t.me/chachachacha99999999", OUT / "telegram-channel.png")

    width, height = 1600, 960
    image = Image.new("RGB", (width, height), "#07111b")
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            ratio = (x / width) * 0.55 + (y / height) * 0.45
            pixels[x, y] = (int(7 + 12 * ratio), int(17 + 16 * ratio), int(27 + 24 * ratio))
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 40):
        draw.line((x, 0, x, height), fill=(18, 38, 53), width=1)
    for y in range(0, height, 40):
        draw.line((0, y, width, y), fill=(18, 38, 53), width=1)

    draw.text((86, 56), "冷咖啡 ColdBrew", font=font(50, True), fill="#f6e7c8")
    draw.text((88, 122), "四模型工作台 · 社区入口", font=font(30), fill="#8fd7e6")
    draw.text((88, 171), "版本通知、问题交流、扫码加入", font=font(22), fill="#aab9c4")
    draw.rounded_rectangle((1260, 64, 1515, 152), radius=28, fill="#102838", outline="#80f0bc", width=2)
    draw.text((1290, 85), "COMMUNITY", font=font(25, True), fill="#80f0bc")
    draw.text((1290, 119), "v8 / 2026", font=font(18), fill="#9ed8e8")

    cards = [
        ("QQ群 · 冷咖啡破甲", "1057540028", "projects/grok4.6-coldbrew/docs/images/qq-group-1.png", "#80f0bc"),
        ("QQ群 · Codex / Claude", "1077074552", "projects/grok4.6-coldbrew/docs/images/qq-group-2.png", "#9aa7ff"),
        ("微信群 · 冷咖啡交流群", "扫码加入（二维码有效期以图片为准）", "projects/grok4.6-coldbrew/docs/images/wechat-group.png", "#ffd68a"),
        ("Telegram · 交流群 / 频道", "点击 README 中的按钮直达", "docs/images/telegram-group.png", "#66d9ff"),
    ]
    card_width, card_height = 700, 280
    positions = [(80, 250), (820, 250), (80, 570), (820, 570)]
    for (title, subtitle, relative_path, accent), (x, y) in zip(cards, positions):
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=28, fill="#0e1c29", outline="#1f3c50", width=2)
        draw.rounded_rectangle((x + 22, y + 22, x + 30, y + card_height - 22), radius=4, fill=accent)
        draw.text((x + 54, y + 34), title, font=font(27, True), fill="#f7f1e3")
        draw.text((x + 54, y + 82), subtitle, font=font(19), fill="#b7c7d0")
        source = ROOT / relative_path
        if source.exists():
            qr_image = Image.open(source).convert("RGB")
            if qr_image.height / qr_image.width > 1.3:
                qr_image = ImageOps.fit(qr_image, (190, 190), method=Image.Resampling.LANCZOS, centering=(0.5, 0.52))
            else:
                qr_image = ImageOps.contain(qr_image, (190, 190), method=Image.Resampling.LANCZOS)
            image.paste(ImageOps.expand(qr_image, border=8, fill="white"), (x + card_width - 235, y + 44))
        if "Telegram" in title:
            draw.text((x + 54, y + 142), "交流群", font=font(18, True), fill="#66d9ff")
            draw.text((x + 54, y + 176), "t.me/chachachacha99999", font=font(18), fill="#d6e7ef")
            draw.text((x + 54, y + 211), "频道", font=font(18, True), fill="#9aa7ff")
            draw.text((x + 54, y + 245), "t.me/chachachacha99999999", font=font(18), fill="#d6e7ef")
        elif "微信" in title:
            draw.text((x + 54, y + 152), "扫码后备注“冷咖啡”", font=font(20), fill="#f6e7c8")
        else:
            draw.text((x + 54, y + 152), "点击 README 中的二维码查看大图", font=font(18), fill="#9fb2bf")
    draw.text((88, 900), "项目主页：github.com/3641397194-wq/gpt5.6-claude-grok4.6-deepseekv4pro", font=font(20), fill="#88a7b5")
    image.save(OUT / "community-board.png")


if __name__ == "__main__":
    main()
