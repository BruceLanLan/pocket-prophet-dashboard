"""Claude Code token 消耗页渲染。

文案刻意不用"额度""已用 x%"这类会被误读为官方订阅配额口径的说法——
那个数据本地拿不到（见 providers/ccusage.py 顶部说明），这里展示的是
本地转录统计出的 token 消耗与近似成本估算。
"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, WHITE, font, gray, hline, new_canvas


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def render(usage: dict):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, 6), "Token 消耗", font=font(16), fill=gray(BLACK))

    draw.text((8, 30), "今日", font=font(13), fill=gray(DARK_GRAY))
    draw.text((8, 46), _fmt_tokens(usage["today_tokens"]), font=font(28), fill=gray(BLACK))

    draw.text((8, 88), f"近5小时 {_fmt_tokens(usage['window_5h_tokens'])}", font=font(13), fill=gray(DARK_GRAY))

    hline(draw, 108)

    y = 116
    by_model = sorted(usage["by_model"].items(), key=lambda kv: -kv[1])
    for model, tok in by_model[:3]:
        label = model if len(model) <= 18 else model[:17] + "…"
        draw.text((8, y), label, font=font(13), fill=gray(BLACK))
        draw.text((150, y), _fmt_tokens(tok), font=font(13), fill=gray(DARK_GRAY))
        y += 18

    draw.text(
        (8, 180), f"今日等价成本估算 ${usage['estimated_cost_usd']:.2f}",
        font=font(13), fill=gray(DARK_GRAY),
    )

    return img
