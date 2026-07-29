"""行情页渲染。版式规格见 docs/PLAN.md Phase 4 步骤 3。

涨跌幅一律用纯黑（灰度 85 在小字号下对比度不足，已在 PLAN.md 里明确禁止）。

每只股票都配一条自己的分时走势线（而不是只给清单里第一只画线），
按股票数量自适应分配竖直空间——清单短的时候每条线画得更大，不会
留出一大片空白；清单变长时自动收缩。最多显示 4 只，超过 4 只的
分页显示尚未实现（PLAN.md 提到但本期未做，超出部分直接截断）。
"""
from datetime import datetime

from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, WHITE, font, gray, new_canvas

MAX_STOCKS = 4
TITLE_Y = 6
CONTENT_Y0 = 28
CONTENT_Y1 = 178
FOOTER_Y = 181
CHART_X0, CHART_X1 = 10, 190
HEADER_LINE_H = 18
BLOCK_GAP = 6


def _draw_sparkline(draw: ImageDraw.ImageDraw, closes, y0: int, y1: int):
    if len(closes) < 2 or y1 - y0 < 6:
        return
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1.0
    n = len(closes)
    xs = [CHART_X0 + i * (CHART_X1 - CHART_X0) / (n - 1) for i in range(n)]
    ys = [y1 - (c - lo) / span * (y1 - y0) for c in closes]
    draw.line(list(zip(xs, ys)), fill=gray(BLACK), width=1)


def render(quotes: list):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, TITLE_Y), "行情", font=font(16), fill=gray(BLACK))

    shown = quotes[:MAX_STOCKS]
    n = len(shown)
    if n == 0:
        draw.text((8, CONTENT_Y0), "暂无数据", font=font(13), fill=gray(DARK_GRAY))
        return img

    block_h = (CONTENT_Y1 - CONTENT_Y0) / n
    f = font(13)

    for i, q in enumerate(shown):
        y_block = CONTENT_Y0 + i * block_h

        draw.text((8, y_block), q["symbol"], font=f, fill=gray(BLACK))
        draw.text((80, y_block), f"{q['price']:.2f}", font=f, fill=gray(BLACK))
        sign = "+" if q["change_pct"] >= 0 else ""
        draw.text((140, y_block), f"{sign}{q['change_pct']:.2f}%", font=f, fill=gray(BLACK))

        chart_y0 = y_block + HEADER_LINE_H
        chart_y1 = y_block + block_h - BLOCK_GAP
        if q["closes"]:
            _draw_sparkline(draw, q["closes"], chart_y0, chart_y1)

    draw.text(
        (8, FOOTER_Y), f"更新 {datetime.now().strftime('%H:%M')}",
        font=font(13), fill=gray(DARK_GRAY),
    )

    return img
