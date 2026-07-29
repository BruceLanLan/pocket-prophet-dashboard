"""新闻页渲染。版式规格见 docs/PLAN.md Phase 4 步骤 4。"""
from PIL import ImageDraw

from renderer.base import BLACK, WHITE, font, gray, new_canvas, truncate_to_width

MAX_LINES = 8
ROW_H = 20
Y0 = 32
MAX_TEXT_WIDTH = 184


def render(titles: list):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((8, 6), "要闻", font=font(16), fill=gray(BLACK))

    f = font(14)
    y = Y0
    for title in titles[:MAX_LINES]:
        line = truncate_to_width(draw, title, f, MAX_TEXT_WIDTH)
        draw.text((8, y), line, font=f, fill=gray(BLACK))
        y += ROW_H

    return img
