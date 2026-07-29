"""天气页渲染。版式规格见 docs/PLAN.md Phase 4 步骤 2。"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, LIGHT_GRAY, WHITE, font, gray, hline, new_canvas, truncate_to_width


def render(data: dict):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((10, 8), data["city"], font=font(22), fill=gray(BLACK))
    draw.text((10, 40), f"{data['temp_c']}°", font=font(52), fill=gray(BLACK))

    desc = truncate_to_width(draw, data["desc"], font(18), 180)
    draw.text((10, 100), desc, font=font(18), fill=gray(BLACK))

    draw.text(
        (10, 126),
        f"湿度 {data['humidity']}%  风 {data['wind_kmph']}km/h",
        font=font(14), fill=gray(DARK_GRAY),
    )

    hline(draw, 152)

    if data["forecast"]:
        parts = [f"{d['min_c']}-{d['max_c']}°" for d in data["forecast"]]
        labels = ["明", "后"][: len(parts)]
        forecast_text = "  ".join(f"{lb} {p}" for lb, p in zip(labels, parts))
        draw.text((10, 160), forecast_text, font=font(13), fill=gray(DARK_GRAY))

    return img
