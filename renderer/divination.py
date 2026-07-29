"""卦象页渲染：六爻爻象 + 本卦/变卦名 + 一句判断。

200x200 屏幕放不下完整装卦断卦（纳甲/六亲/世应），按 docs/PLAN.md 的范围
边界，这里只画：六条爻线（阳爻实线、阴爻断线、动爻加标记）、本卦名、
变卦名（若有动爻）、GUA_READING 里查到的一句判断。
"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, LIGHT_GRAY, WHITE, font, gray, hline, new_canvas, truncate_to_width

ROW_TOP_Y = [8, 23, 38, 53, 68, 83]  # 6 行，从上到下；行0 对应上爻，行5 对应初爻
BAR_X0, BAR_X1 = 25, 175
YIN_GAP = 12  # 阴爻断开的间隙半宽
BAR_THICK = 7


def _draw_line(draw: ImageDraw.ImageDraw, row_top: int, is_yang: bool, is_changing: bool):
    y0 = row_top + 1
    y1 = y0 + BAR_THICK
    color = gray(BLACK)
    if is_yang:
        draw.rectangle([BAR_X0, y0, BAR_X1, y1], fill=color)
    else:
        mid = (BAR_X0 + BAR_X1) // 2
        draw.rectangle([BAR_X0, y0, mid - YIN_GAP, y1], fill=color)
        draw.rectangle([mid + YIN_GAP, y0, BAR_X1, y1], fill=color)

    if is_changing:
        cy = (y0 + y1) // 2
        cx = BAR_X1 + 12
        r = 5
        if is_yang:
            # 老阳：动而变阴，画空心圆
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        else:
            # 老阴：动而变阳，画叉
            draw.line([(cx - r, cy - r), (cx + r, cy + r)], fill=color, width=2)
            draw.line([(cx - r, cy + r), (cx + r, cy - r)], fill=color, width=2)


def render(cast: dict):
    """cast: providers.liuyao.cast_hexagram() 的返回值。"""
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    lines = cast["lines"]  # 索引0=初爻 ... 索引5=上爻
    for row, line in enumerate(lines[::-1]):  # 反转：行0画上爻，行5画初爻
        _draw_line(draw, ROW_TOP_Y[row], line["is_yang"], line["is_changing"])

    hline(draw, 98, fill=LIGHT_GRAY)

    if cast["变卦"]:
        title = f"{cast['本卦']} → {cast['变卦']}"
    else:
        title = f"{cast['本卦']}（不变）"
    f_title = font(15)
    title = truncate_to_width(draw, title, f_title, 180)
    draw.text((10, 104), title, font=f_title, fill=gray(BLACK))

    judgment = cast.get("判断") or ""
    f_judge = font(13)
    y = 128
    # 简单按宽度分两行
    if draw.textlength(judgment, font=f_judge) <= 180:
        draw.text((10, y), judgment, font=f_judge, fill=gray(DARK_GRAY))
    else:
        mid = len(judgment) // 2
        # 在中点附近找一个不拆词的断点（優先句读符号）
        split_at = judgment.rfind("——", 0, mid + 3)
        if split_at == -1:
            split_at = mid
        else:
            split_at += 2
        line1 = truncate_to_width(draw, judgment[:split_at], f_judge, 180)
        line2 = truncate_to_width(draw, judgment[split_at:], f_judge, 180)
        draw.text((10, y), line1, font=f_judge, fill=gray(DARK_GRAY))
        draw.text((10, y + 17), line2, font=f_judge, fill=gray(DARK_GRAY))

    if cast["动爻"]:
        mv_text = "动爻：" + "、".join(str(i) for i in cast["动爻"])
    else:
        mv_text = "六爻不动"
    f_mv = font(13)
    draw.text((10, 178), mv_text, font=f_mv, fill=gray(DARK_GRAY))

    return img
