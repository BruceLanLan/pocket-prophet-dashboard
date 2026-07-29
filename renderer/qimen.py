"""奇门遁甲九宫格渲染。

版式经可读性实测确认（docs/PLAN-v2.md Phase 8 步骤 1）：每宫 63×55px，
13px 字号 3 行清晰可辨。据此砍掉了八神这一层——宫名/门/星/干支四类信息
压进三行：第一行宫名，第二行"门 星"（星名取去掉"天"字的那个字），
第三行"地干/天干"。200×200 放不下断语解释，只给一句话收尾。
"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, LIGHT_GRAY, WHITE, font, gray, hline, new_canvas, truncate_to_width

GRID_X0, GRID_Y0 = 4, 24
GRID_X1, GRID_Y1 = 196, 180
CELL_W = (GRID_X1 - GRID_X0) / 3
CELL_H = (GRID_Y1 - GRID_Y0) / 3
FOOTER_Y = 183


def _draw_cell(draw: ImageDraw.ImageDraw, cx: float, cy: float, cell: dict, f):
    border = gray(BLACK) if cell.get("is_zhi_fu") else gray(LIGHT_GRAY)
    draw.rectangle([cx, cy, cx + CELL_W, cy + CELL_H], outline=border, width=2 if cell.get("is_zhi_fu") else 1)

    if cell["is_zhong"]:
        draw.text((cx + 3, cy + 2), "中", font=f, fill=gray(BLACK))
        draw.text((cx + 3, cy + 18), cell["star"][-1], font=f, fill=gray(BLACK))
        note = cell.get("note", "")
        if note:
            draw.text((cx + 3, cy + 34), note[:4], font=f, fill=gray(DARK_GRAY))
        return

    draw.text((cx + 3, cy + 2), cell["direction"], font=f, fill=gray(DARK_GRAY))
    draw.text((cx + 3, cy + 18), f"{cell['men']} {cell['star'][-1]}", font=f, fill=gray(BLACK))
    gan = cell["di_gan"] if cell["di_gan"] == cell["tian_gan"] else f"{cell['di_gan']}/{cell['tian_gan']}"
    draw.text((cx + 3, cy + 34), gan, font=f, fill=gray(DARK_GRAY))


def render(cast: dict):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    header = f"{cast['dt'].strftime('%H:%M')} {cast['ju']}"
    draw.text((6, 4), header, font=font(13), fill=gray(BLACK))
    hline(draw, 20)

    f13 = font(13)
    for i, cell in enumerate(cast["cells"]):
        r, c = divmod(i, 3)
        _draw_cell(draw, GRID_X0 + c * CELL_W, GRID_Y0 + r * CELL_H, cell, f13)

    footer = f"值符：{cast['zhi_fu_star']}（{cast['zhi_fu_gong']}宫，粗框标注）"
    footer = truncate_to_width(draw, footer, f13, 188)
    draw.text((6, FOOTER_Y), footer, font=f13, fill=gray(DARK_GRAY))

    return img
