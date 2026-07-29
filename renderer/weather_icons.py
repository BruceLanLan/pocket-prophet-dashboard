"""极简天气图标：纯 PIL 几何图形，不用外部图标字体。

理由（docs/PLAN-v2.md Phase 9 步骤 1）：位图图标字体在 200×200、4 级灰阶
下容易糊成一团，几何图形描边+实心块在小尺寸抖动下轮廓更干净。

天气代码来自 wttr.in 的 weatherCode 字段，即 worldweatheronline 的标准
天气代码表（不是 wttr.in 自定义的）。CODE_TO_CATEGORY 覆盖常见分类，
未匹配的代码一律落到 "cloudy"（阴，最保守的兜底，不会误报晴天或雨天）。
"""
import math

from renderer.base import BLACK, WHITE, gray

CATEGORIES = ("sunny", "partly_cloudy", "cloudy", "rain", "snow", "fog", "thunder")

# worldweatheronline 天气代码 -> 简化分类。完整代码表见
# https://www.worldweatheronline.com/weather-api/api/docs/weather-icons.aspx
CODE_TO_CATEGORY = {
    "113": "sunny",
    "116": "partly_cloudy",
    "119": "cloudy", "122": "cloudy",
    "143": "fog", "248": "fog", "260": "fog",
    "176": "rain", "263": "rain", "266": "rain", "281": "rain", "284": "rain",
    "293": "rain", "296": "rain", "299": "rain", "302": "rain", "305": "rain",
    "308": "rain", "311": "rain", "314": "rain", "353": "rain", "356": "rain", "359": "rain",
    "200": "thunder", "386": "thunder", "389": "thunder", "392": "thunder", "395": "thunder",
    "227": "snow", "230": "snow", "317": "snow", "320": "snow", "323": "snow", "326": "snow",
    "329": "snow", "332": "snow", "335": "snow", "338": "snow", "350": "snow",
    "362": "snow", "365": "snow", "368": "snow", "371": "snow", "374": "snow", "377": "snow",
}


def category_for(code: str) -> str:
    return CODE_TO_CATEGORY.get(str(code), "cloudy")


def _cloud_bbox(box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    return x0, y0, w, h


def _draw_cloud(draw, box, fill):
    x0, y0, w, h = _cloud_bbox(box)
    base_y0 = y0 + h * 0.42
    base_y1 = y0 + h * 0.82
    draw.ellipse([x0 + w * 0.05, base_y0, x0 + w * 0.62, base_y1], fill=fill)
    draw.ellipse([x0 + w * 0.30, y0 + h * 0.20, x0 + w * 0.80, base_y1 - h * 0.05], fill=fill)
    draw.rectangle([x0 + w * 0.18, base_y0 + (base_y1 - base_y0) * 0.35, x0 + w * 0.75, base_y1], fill=fill)


def _draw_sun(draw, box, ray=True, cx_frac=0.45, cy_frac=0.42, r_frac=0.22):
    x0, y0, w, h = _cloud_bbox(box)
    cx, cy = x0 + w * cx_frac, y0 + h * cy_frac
    r = min(w, h) * r_frac
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gray(BLACK))
    if ray:
        for i in range(8):
            ang = i * math.pi / 4
            x_s, y_s = cx + math.cos(ang) * r * 1.4, cy + math.sin(ang) * r * 1.4
            x_e, y_e = cx + math.cos(ang) * r * 2.0, cy + math.sin(ang) * r * 2.0
            draw.line([(x_s, y_s), (x_e, y_e)], fill=gray(BLACK), width=2)


def _draw_drops(draw, box, n=3):
    x0, y0, w, h = _cloud_bbox(box)
    base_y = y0 + h * 0.82
    for i in range(n):
        x = x0 + w * (0.20 + i * 0.22)
        draw.line([(x, base_y + 2), (x - 4, base_y + 12)], fill=gray(BLACK), width=2)


def _draw_flakes(draw, box, n=3):
    x0, y0, w, h = _cloud_bbox(box)
    base_y = y0 + h * 0.86
    for i in range(n):
        cx = x0 + w * (0.22 + i * 0.22)
        cy = base_y + 6
        r = 3
        draw.line([(cx - r, cy), (cx + r, cy)], fill=gray(BLACK), width=2)
        draw.line([(cx, cy - r), (cx, cy + r)], fill=gray(BLACK), width=2)
        draw.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)], fill=gray(BLACK), width=1)
        draw.line([(cx - r * 0.7, cy + r * 0.7), (cx + r * 0.7, cy - r * 0.7)], fill=gray(BLACK), width=1)


def _draw_bolt_cutout(draw, box):
    """闪电画成云朵实心区域里的白色镂空，而不是叠在云上方——不然黑色
    闪电画在黑色云上会完全不可见（早期版本踩过这个坑）。"""
    x0, y0, w, h = _cloud_bbox(box)
    pts = [
        (x0 + w * 0.52, y0 + h * 0.45),
        (x0 + w * 0.38, y0 + h * 0.66),
        (x0 + w * 0.48, y0 + h * 0.66),
        (x0 + w * 0.40, y0 + h * 0.80),
        (x0 + w * 0.60, y0 + h * 0.58),
        (x0 + w * 0.50, y0 + h * 0.58),
    ]
    draw.polygon(pts, fill=gray(WHITE))


def _draw_fog(draw, box):
    x0, y0, w, h = _cloud_bbox(box)
    for i, frac in enumerate((0.35, 0.52, 0.69, 0.86)):
        y = y0 + h * frac
        inset = w * (0.05 if i % 2 == 0 else 0.16)
        draw.line([(x0 + inset, y), (x0 + w - inset, y)], fill=gray(BLACK), width=3)


def draw(draw_ctx, category: str, box):
    """在 box=(x0,y0,x1,y1) 范围内画一个天气图标。"""
    if category == "sunny":
        _draw_sun(draw_ctx, box, ray=True)
    elif category == "partly_cloudy":
        # 太阳挪到左上角、缩小、不带光芒；云挪到右下角，两者不重叠——
        # 早期版本让两者同心叠放、只画云的部分描边，结果糊成两个空心圆圈。
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        _draw_sun(draw_ctx, box, ray=False, cx_frac=0.30, cy_frac=0.30, r_frac=0.18)
        sub_box = (x0 + w * 0.30, y0 + h * 0.30, x1 + w * 0.05, y1 + h * 0.05)
        _draw_cloud(draw_ctx, sub_box, fill=gray(BLACK))
    elif category == "cloudy":
        _draw_cloud(draw_ctx, box, fill=gray(BLACK))
    elif category == "rain":
        _draw_cloud(draw_ctx, box, fill=gray(BLACK))
        _draw_drops(draw_ctx, box)
    elif category == "snow":
        _draw_cloud(draw_ctx, box, fill=gray(BLACK))
        _draw_flakes(draw_ctx, box)
    elif category == "thunder":
        _draw_cloud(draw_ctx, box, fill=gray(BLACK))
        _draw_bolt_cutout(draw_ctx, box)
    elif category == "fog":
        _draw_fog(draw_ctx, box)
    else:
        _draw_cloud(draw_ctx, box, fill=gray(BLACK))
