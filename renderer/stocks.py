"""行情页渲染。版式规格见 docs/PLAN.md Phase 4 步骤 3。

涨跌幅一律用纯黑（灰度 85 在小字号下对比度不足，已在 PLAN.md 里明确禁止）。
走势线取清单第一个标的的当日分时收盘价。
"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, WHITE, font, gray, new_canvas

MAX_ROWS = 5
ROW_H = 22
ROW_START_Y = 30
SPARKLINE_Y0, SPARKLINE_Y1 = 165, 195
SPARKLINE_X0, SPARKLINE_X1 = 10, 190


def _draw_sparkline(draw: ImageDraw.ImageDraw, closes):
    if len(closes) < 2:
        return
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1.0
    n = len(closes)
    xs = [SPARKLINE_X0 + i * (SPARKLINE_X1 - SPARKLINE_X0) / (n - 1) for i in range(n)]
    ys = [SPARKLINE_Y1 - (c - lo) / span * (SPARKLINE_Y1 - SPARKLINE_Y0) for c in closes]
    draw.line(list(zip(xs, ys)), fill=gray(BLACK), width=1)


def render(quotes: list):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, 6), "行情", font=font(16), fill=gray(BLACK))

    y = ROW_START_Y
    for q in quotes[:MAX_ROWS]:
        draw.text((8, y), q["symbol"], font=font(13), fill=gray(BLACK))
        draw.text((80, y), f"{q['price']:.2f}", font=font(13), fill=gray(BLACK))
        sign = "+" if q["change_pct"] >= 0 else ""
        draw.text((140, y), f"{sign}{q['change_pct']:.2f}%", font=font(13), fill=gray(BLACK))
        y += ROW_H

    if quotes and quotes[0]["closes"]:
        draw.text(
            (8, SPARKLINE_Y0 - 18), f"{quotes[0]['symbol']} 分时",
            font=font(13), fill=gray(DARK_GRAY),
        )
        _draw_sparkline(draw, quotes[0]["closes"])

    return img
