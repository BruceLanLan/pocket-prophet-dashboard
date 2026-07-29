"""天气页渲染。

Phase 9 改版：图标 + 温度并排（原版式温度独占一行，图标腾出的横向空间
用来放体感温度和降水概率，这两项之前完全没地方放）。
"""
from PIL import ImageDraw

from renderer.base import BLACK, DARK_GRAY, WHITE, font, gray, hline, new_canvas, truncate_to_width
from renderer import weather_icons

ICON_BOX = (8, 34, 78, 100)  # 图标区域


def render(data: dict):
    img = new_canvas(bg=WHITE)
    draw = ImageDraw.Draw(img)

    draw.text((10, 6), data["city"], font=font(22), fill=gray(BLACK))

    weather_icons.draw(draw, weather_icons.category_for(data["code"]), ICON_BOX)
    draw.text((86, 44), f"{data['temp_c']}°", font=font(44), fill=gray(BLACK))

    desc = truncate_to_width(draw, data["desc"], font(16), 180)
    draw.text((10, 104), desc, font=font(16), fill=gray(BLACK))

    draw.text(
        (10, 128),
        f"体感 {data['feels_like_c']}°  降水 {data['chance_of_rain']}%",
        font=font(14), fill=gray(DARK_GRAY),
    )
    draw.text(
        (10, 146),
        f"湿度 {data['humidity']}%  风 {data['wind_kmph']}km/h",
        font=font(14), fill=gray(DARK_GRAY),
    )

    hline(draw, 166)

    if data["forecast"]:
        parts = [f"{d['min_c']}-{d['max_c']}°" for d in data["forecast"]]
        labels = ["明", "后"][: len(parts)]
        forecast_text = "  ".join(f"{lb} {p}" for lb, p in zip(labels, parts))
        draw.text((10, 174), forecast_text, font=font(13), fill=gray(DARK_GRAY))

    return img
