"""行情页渲染，两种版式（docs/PLAN-v2.md Phase 10）：

- `render`（多只概览）：每只股票一行 + 自己的分时线，按数量自适应空间
- `render_detail`（单只详情）：一只股票占满整屏，大号现价 + 走势线 +
  成交量/52周区间。默认取股票清单第一只。

涨跌幅一律用纯黑（灰度 85 在小字号下对比度不足，PLAN.md 已禁止）。

关于"参考 TradingView widget"：拿不到那些 widget 实际截图，做不了视觉
复刻。这两版遵循的是信息层级原则——一个主导数字，其余全部次级——而不是
具体样式，这条原则不需要看过原版设计也能用。
"""
from datetime import datetime

from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, WHITE, font, gray, hline, new_canvas

MAX_STOCKS = 4
TITLE_Y = 6
CONTENT_Y0 = 28
CONTENT_Y1 = 178
FOOTER_Y = 181
CHART_X0, CHART_X1 = 10, 190
HEADER_LINE_H = 18
BLOCK_GAP = 6


def _draw_sparkline(draw: ImageDraw.ImageDraw, closes, y0: int, y1: int, x0=CHART_X0, x1=CHART_X1):
    if len(closes) < 2 or y1 - y0 < 6:
        return
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1.0
    n = len(closes)
    xs = [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]
    ys = [y1 - (c - lo) / span * (y1 - y0) for c in closes]
    draw.line(list(zip(xs, ys)), fill=gray(BLACK), width=1)


def _fmt_volume(v):
    if v is None:
        return "—"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}K"
    return str(v)


SECONDARY_LINE_MIN_BLOCK_H = 55  # 低于这个块高就不加成交量/今日区间那一行，
                                  # 优先保住走势线的可读性（清单越长块越矮）


def render(quotes: list):
    """多只概览：每只一行 + 各自的分时线。

    早期版本只有 符号/现价/涨跌% 一行 + 一条光走势线，用户反馈"显示的内容
    很空"——留白确实多：走势线没有任何数值参照，块高够大时也没利用多出来
    的空间。块高够大（n<=2，两只股票时最明显）时现在会加一行紧凑信息
    （今日区间 + 成交量）；清单变长、块变矮时才退回原来的极简版式，
    优先保住走势线本身的可读性而不是硬塞文字。
    """
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, TITLE_Y), "行情", font=font(16), fill=gray(BLACK))

    shown = quotes[:MAX_STOCKS]
    n = len(shown)
    if n == 0:
        draw.text((8, CONTENT_Y0), "暂无数据", font=font(13), fill=gray(DARK_GRAY))
        return img

    block_h = (CONTENT_Y1 - CONTENT_Y0) / n
    show_secondary = block_h >= SECONDARY_LINE_MIN_BLOCK_H
    f = font(13)

    for i, q in enumerate(shown):
        y_block = CONTENT_Y0 + i * block_h

        draw.text((8, y_block), q["symbol"], font=f, fill=gray(BLACK))
        draw.text((80, y_block), f"{q['price']:.2f}", font=f, fill=gray(BLACK))
        sign = "+" if q["change_pct"] >= 0 else ""
        draw.text((140, y_block), f"{sign}{q['change_pct']:.2f}%", font=f, fill=gray(BLACK))

        y_cursor = y_block + HEADER_LINE_H
        if show_secondary:
            lo_c, hi_c = (min(q["closes"]), max(q["closes"])) if q["closes"] else (None, None)
            parts = []
            if lo_c is not None:
                parts.append(f"今日 {lo_c:.1f}-{hi_c:.1f}")
            if q.get("volume") is not None:
                parts.append(f"量 {_fmt_volume(q['volume'])}")
            if parts:
                draw.text((8, y_cursor), "  ".join(parts), font=f, fill=gray(DARK_GRAY))
            y_cursor += 16

        chart_y0 = y_cursor
        chart_y1 = y_block + block_h - BLOCK_GAP
        if q["closes"] and chart_y1 - chart_y0 >= 10:
            _draw_sparkline(draw, q["closes"], chart_y0, chart_y1)

    draw.text(
        (8, FOOTER_Y), f"更新 {datetime.now().strftime('%H:%M')}",
        font=font(13), fill=gray(DARK_GRAY),
    )

    return img


def render_detail(quote: dict):
    """单只详情：一只股票占满整屏。"""
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((10, 6), quote["symbol"], font=font(18), fill=gray(BLACK))
    name = quote.get("name") or ""
    if name and name != quote["symbol"]:
        draw.text((10, 27), name[:16], font=font(13), fill=gray(DARK_GRAY))

    draw.text((10, 46), f"{quote['price']:.2f}", font=font(46), fill=gray(BLACK))

    sign = "+" if quote["change_pct"] >= 0 else ""
    draw.text((10, 98), f"{sign}{quote['change_pct']:.2f}%", font=font(20), fill=gray(BLACK))

    hline(draw, 126)

    if quote["closes"]:
        _draw_sparkline(draw, quote["closes"], 132, 172, x0=10, x1=190)

    w52_lo, w52_hi = quote.get("week52_low"), quote.get("week52_high")
    if w52_lo is not None and w52_hi is not None:
        draw.text((10, 178), f"52周 {w52_lo:.0f}-{w52_hi:.0f}", font=font(13), fill=gray(DARK_GRAY))
    vol = _fmt_volume(quote.get("volume"))
    draw.text((110, 178), f"量 {vol}", font=font(13), fill=gray(DARK_GRAY))

    return img
