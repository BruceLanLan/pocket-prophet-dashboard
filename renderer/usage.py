"""Claude Code token 消耗页渲染，Phase 12 重设计。

口径问题（必须先讲清楚，docs/PLAN-v2.md Phase 12）：用户想要"以百分比显示
还剩多少用量"，但官方订阅额度百分比本地拿不到（providers/ccusage.py 顶部
已确认）。这里显示的百分比是"今日 token 消耗 / 用户自设预算"，**预算数值
本身也画在屏幕上**，让人一眼看出这是自设基准，不是官方口径——不做一个看起来
像官方数据的百分比。

关于吉祥物：Claude 没有官方吉祥物角色，有的是星芒（asterisk）标记。这里画
的是一个抽象几何星芒符号当视觉锚点，不虚构人物/动物形象。
"""
import math

from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, LIGHT_GRAY, WHITE, font, gray, hline, new_canvas

RING_BBOX = (50, 28, 150, 128)
RING_WIDTH = 10


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _draw_ring(draw: ImageDraw.ImageDraw, pct: float):
    draw.arc(RING_BBOX, 0, 360, fill=gray(LIGHT_GRAY), width=RING_WIDTH)
    sweep = max(0.0, min(pct, 1.0)) * 360
    if sweep > 0:
        draw.arc(RING_BBOX, -90, -90 + sweep, fill=gray(BLACK), width=RING_WIDTH)


def _draw_asterisk_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float):
    """抽象星芒符号（视觉锚点），不是具体角色形象——见模块顶部说明。"""
    for i in range(6):
        ang = i * math.pi / 3 - math.pi / 2
        x0, y0 = cx - math.cos(ang) * r, cy - math.sin(ang) * r
        x1, y1 = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        draw.line([(x0, y0), (x1, y1)], fill=gray(DARK_GRAY), width=2)


def render(usage: dict, daily_budget: int):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, 6), "Token 用量", font=font(16), fill=gray(BLACK))
    _draw_asterisk_mark(draw, 186, 13, 7)

    budget = daily_budget or 1
    pct = usage["today_tokens"] / budget
    _draw_ring(draw, pct)

    pct_label = f"{pct*100:.0f}%"
    f_pct = font(28)
    bbox = draw.textbbox((0, 0), pct_label, font=f_pct)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cx, cy = (RING_BBOX[0] + RING_BBOX[2]) / 2, (RING_BBOX[1] + RING_BBOX[3]) / 2
    draw.text((cx - tw / 2, cy - th / 2 - bbox[1]), pct_label, font=f_pct, fill=gray(BLACK))

    budget_label = f"预算 {_fmt_tokens(daily_budget)}（自设）"
    f13 = font(13)
    bl_bbox = draw.textbbox((0, 0), budget_label, font=f13)
    draw.text((100 - (bl_bbox[2] - bl_bbox[0]) / 2, 134), budget_label, font=f13, fill=gray(DARK_GRAY))

    detail = f"今日 {_fmt_tokens(usage['today_tokens'])} · 近5h {_fmt_tokens(usage['window_5h_tokens'])}"
    d_bbox = draw.textbbox((0, 0), detail, font=f13)
    draw.text((100 - (d_bbox[2] - d_bbox[0]) / 2, 154), detail, font=f13, fill=gray(BLACK))

    hline(draw, 174)
    draw.text(
        (8, 180), f"今日等价成本估算 ${usage['estimated_cost_usd']:.2f}",
        font=f13, fill=gray(DARK_GRAY),
    )

    return img
