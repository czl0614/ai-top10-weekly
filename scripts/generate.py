# -*- coding: utf-8 -*-
"""生成 AI 生产力应用 TOP10 海报（跨平台：Windows / Linux CI 均可运行）"""
import os
import re
import json
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 1800
S = 2
IMG_H = 780
FOCUS_Y = 0.42


def _pick(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


FONT_CANDIDATES = {
    "bold": [
        r"C:\Windows\Fonts\msyhbd.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "reg": [
        r"C:\Windows\Fonts\msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
    "light": [
        r"C:\Windows\Fonts\msyhl.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ],
    "mono": [
        r"C:\Windows\Fonts\consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ],
    "mono_b": [
        r"C:\Windows\Fonts\consolab.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ],
}

FONTS = {}
for k, cands in FONT_CANDIDATES.items():
    hit = _pick(*cands)
    if not hit:
        raise RuntimeError(f"找不到字体：{k}，请安装 fonts-noto-cjk")
    FONTS[k] = hit


def F(kind, size):
    return ImageFont.truetype(FONTS[kind], size * S)


def stamp(text):
    """副标题里的「数据截至 YYYY.MM.DD」自动换成运行当天，避免每周推同一张旧日期"""
    today = datetime.date.today().strftime("%Y.%m.%d")
    return re.sub(r"数据截至\s*\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", f"数据截至 {today}", text)


def load_bg(path, box_w, box_h, focus_y):
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    scale = max(box_w / iw, box_h / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - box_w) // 2
    top = int((nh - box_h) * focus_y)
    return im.crop((left, top, left + box_w, top + box_h))


def vgrad(bg, y0, y1, color, a0, a1):
    ov = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    n = int((y1 - y0) * S)
    for i in range(n):
        t = i / max(1, n - 1)
        a = int(a0 + (a1 - a0) * (t ** 0.8))
        od.line([(0, y0 * S + i), (W * S, y0 * S + i)], fill=(*color, a))
    return Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")


def build(data, out_path):
    bg_path = os.path.join(ROOT, "assets", "bg.jpg")
    img = load_bg(bg_path, W * S, IMG_H * S, FOCUS_Y)

    INK, SUB, MUT = (16, 20, 30), (72, 78, 92), (128, 132, 144)
    ACC, ACC2 = (18, 82, 176), (120, 148, 190)
    SCRIM = (246, 249, 253)

    canvas = Image.new("RGB", (W * S, H * S), SCRIM)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    img = ImageEnhance.Color(img).enhance(0.95)
    canvas.paste(img, (0, 0))
    canvas = vgrad(canvas, 0, 390, SCRIM, 232, 0)
    canvas = vgrad(canvas, IMG_H - 150, IMG_H + 20, SCRIM, 0, 250)
    d = ImageDraw.Draw(canvas, "RGBA")

    f_kick = F("mono_b", 14)
    f_h1 = F("bold", 64)
    f_h1l = F("light", 64)
    f_sub = F("reg", 19)
    f_rank = F("mono_b", 28)
    f_name = F("bold", 27)
    f_cn = F("reg", 19)
    f_tag = F("reg", 14)
    f_met = F("bold", 17)
    f_foot = F("reg", 13)

    M = 86
    TY = 124

    def t(xy, s, f, fill, anchor="la"):
        d.text((xy[0] * S, xy[1] * S), s, font=f, fill=fill, anchor=anchor)

    def ln(p1, p2, fill, w=1):
        d.line([p1[0] * S, p1[1] * S, p2[0] * S, p2[1] * S], fill=fill, width=int(w * S))

    t((M, TY - 56), "AI PRODUCTIVITY  ·  WEEKLY", f_kick, ACC)
    ln((M, TY - 26), (W - M, TY - 26), (*ACC2, 130), 1)

    stroke = (255, 255, 255, 215)
    sw = 4 * S
    d.text((M * S, TY * S), data["title_main"], font=f_h1, fill=INK,
           stroke_width=sw, stroke_fill=stroke)
    w1 = d.textlength(data["title_main"], font=f_h1) / S
    d.text(((M + w1 + 14) * S, TY * S), data["title_accent"], font=f_h1l, fill=ACC,
           stroke_width=sw, stroke_fill=stroke)
    # 副标题压在照片上，必须自带白色描边，否则遇到亮部/暗部都会糊掉
    d.text((M * S, (TY + 92) * S), stamp(data["subtitle"]), font=f_sub, fill=SUB,
           stroke_width=2 * S, stroke_fill=(255, 255, 255, 242))
    ln((0, IMG_H), (W, IMG_H), (*ACC, 90), 1)

    items = data["items"]
    TOP = IMG_H + 44
    ROW = max(78, int((H - TOP - 62) / len(items)))
    RX, NX = M, M + 56
    TAG_X = W - M - 196
    MET_X = W - M

    ln((M, TOP - 18), (W - M, TOP - 18), (*ACC2, 150), 1)

    for i, it in enumerate(items):
        y = TOP + i * ROW
        if i < 3:
            d.rounded_rectangle([(M - 18) * S, (y - 10) * S, (W - M + 18) * S, (y + 92) * S],
                                radius=10 * S, fill=(*ACC, 14))
        t((RX, y + 4), f"{i+1:02d}", f_rank, ACC if i < 3 else MUT)
        d.rounded_rectangle([(RX - 12) * S, (y + 8) * S, (RX - 9) * S, (y + 36) * S],
                            radius=2 * S, fill=(*(ACC if i < 3 else ACC2), 230))
        t((NX, y), it["name"], f_name, INK)
        t((NX, y + 34), it["cn"], f_cn, SUB)

        tag = it.get("tag", "")
        if tag:
            tw = d.textlength(tag, font=f_tag) / S
            bx = TAG_X - (tw + 20)
            d.rounded_rectangle([bx * S, (y + 5) * S, (bx + tw + 20) * S, (y + 31) * S],
                                radius=6 * S, fill=(*ACC, 22), outline=(*ACC, 110), width=1 * S)
            t((bx + 10, y + 9), tag, f_tag, ACC)

        t((MET_X, y + 4), it["metric"], f_met, ACC, anchor="ra")

        if i < len(items) - 1:
            yy = y + 86
            x = NX
            while x < W - M:
                d.line([x * S, yy * S, min(x + 2, W - M) * S, yy * S],
                       fill=(*ACC2, 85), width=1 * S)
                x += 8

    fy = TOP + len(items) * ROW + 14
    ln((M, fy), (W - M, fy), (*ACC2, 130), 1)
    t((M, fy + 16), data["footer"], f_foot, SUB)

    canvas.resize((W, H), Image.LANCZOS).save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    with open(os.path.join(ROOT, "data", "ai_top10.json"), "r", encoding="utf-8") as f:
        d = json.load(f)
    out = build(d, os.path.join(ROOT, "poster.png"))
    print("generated:", out)
