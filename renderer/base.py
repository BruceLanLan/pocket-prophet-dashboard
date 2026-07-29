"""渲染公共原语：200x200 画布、四级灰阶调色板、字体、文本截断。

规格来源 docs/ARCHITECTURE.md §1.4 / §2.3（实测确认，非推测）：
- 面板分辨率 200x200，4 级灰阶 {0,85,170,255}
- 13px 中文可读，14px 舒适，13px 是下限
- 关键数字用纯黑 0，灰度 85 只用于次要信息（对比度会明显下降）
"""
import os

from PIL import Image, ImageDraw, ImageFont

WIDTH = HEIGHT = 200

BLACK = 0
DARK_GRAY = 85
LIGHT_GRAY = 170
WHITE = 255

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
MIN_FONT_SIZE = 13

_font_cache = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    if size < MIN_FONT_SIZE:
        raise ValueError(f"字号 {size} 低于可读下限 {MIN_FONT_SIZE}px（见 ARCHITECTURE.md §2.3）")
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]


def new_canvas(bg=WHITE) -> Image.Image:
    return Image.new("RGB", (WIDTH, HEIGHT), (bg, bg, bg))


def gray(v: int):
    return (v, v, v)


def truncate_to_width(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> str:
    """按实际渲染宽度截断（中英文混排字宽不同，不能按字符数算）。"""
    if draw.textlength(text, font=fnt) <= max_width:
        return text
    ellipsis = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid] + ellipsis
        if draw.textlength(candidate, font=fnt) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis


def hline(draw: ImageDraw.ImageDraw, y: int, x0: int = 10, x1: int = WIDTH - 10, fill=LIGHT_GRAY):
    draw.line([(x0, y), (x1, y)], fill=gray(fill), width=1)
