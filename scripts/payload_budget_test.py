"""Test whether realistic dashboard images fit under the device's 14336 upload cap."""
import base64
import io
import json
import requests
from PIL import Image, ImageDraw, ImageFont

W = H = 200
CONVERT = "https://dot.mindreset.tech/api/authV2/device/render/convert"
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"

def font(sz):
    return ImageFont.truetype(FONT, sz)

def to_data_url(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def convert(img, kernel):
    body = {"series": "rand", "model": "rand_0", "edition": 1,
            "image": to_data_url(img), "colorLevels": 4,
            "ditherType": "DIFFUSION", "ditherKernel": kernel}
    r = requests.post(CONVERT, json=body, timeout=25)
    if r.status_code != 200:
        return None, r.status_code
    return r.json().get("COMPRESS_ARRAY_V2", ""), 200

# --- Mock A: weather panel, flat design (pure black/white, no photo) ---
def mock_weather():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 8), "深圳", font=font(22), fill=(0, 0, 0))
    d.text((10, 40), "28°", font=font(52), fill=(0, 0, 0))
    d.text((10, 100), "多云转晴", font=font(18), fill=(0, 0, 0))
    d.text((10, 126), "湿度 72%  风 3级", font=font(14), fill=(85, 85, 85))
    d.line([(10, 152), (190, 152)], fill=(170, 170, 170), width=1)
    d.text((10, 160), "明 26-31°  后 25-30°", font=font(13), fill=(85, 85, 85))
    d.text((10, 180), "19:20 更新", font=font(11), fill=(170, 170, 170))
    return img

# --- Mock B: stock panel, dense text + a sparkline ---
def mock_stocks():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((8, 6), "行情", font=font(16), fill=(0, 0, 0))
    rows = [("上证指数", "3412.5", "+0.82%"), ("恒生指数", "24180", "-0.31%"),
            ("贵州茅台", "1580.0", "+1.24%"), ("BTC", "94820", "+2.10%"),
            ("英伟达", "182.4", "-0.55%")]
    y = 30
    for name, price, chg in rows:
        d.text((8, y), name, font=font(13), fill=(0, 0, 0))
        d.text((96, y), price, font=font(13), fill=(0, 0, 0))
        d.text((150, y), chg, font=font(12), fill=(85, 85, 85))
        y += 22
    pts = [(8 + i * 6, 190 - (i * 7 % 23)) for i in range(31)]
    d.line(pts, fill=(0, 0, 0), width=1)
    return img

# --- Mock C: news headlines, densest text case ---
def mock_news():
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((8, 6), "要闻", font=font(16), fill=(0, 0, 0))
    lines = ["央行宣布下调存款准备", "金率0.5个百分点", "国常会部署稳外贸新",
             "举措十六条", "OpenAI发布新一代推", "理模型定价下调40%",
             "台风路径西调预计明", "日登陆粤东沿海"]
    y = 32
    for ln in lines:
        d.text((8, y), ln, font=font(14), fill=(0, 0, 0))
        y += 20
    return img

# --- Mock D: worst case, photo-like gradient (should blow the budget) ---
def mock_gradient():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for x in range(W):
        for y in range(H):
            v = int((x * 0.7 + y * 0.6) % 256)
            px[x, y] = (v, v, v)
    return img

cases = [("weather_flat", mock_weather()), ("stocks_dense", mock_stocks()),
         ("news_densest", mock_news()), ("gradient_worstcase", mock_gradient())]

CAP = 14336
print(f"{'case':<20} {'kernel':<18} {'b64_len':>8} {'vs_cap':>10}")
print("-" * 60)
results = {}
for name, img in cases:
    for kernel in ["THRESHOLD", "FLOYD_STEINBERG"]:
        arr, code = convert(img, kernel)
        if arr is None:
            print(f"{name:<20} {kernel:<18} HTTP {code}")
            continue
        n = len(arr)
        verdict = "OK" if n <= CAP else "OVER!"
        print(f"{name:<20} {kernel:<18} {n:>8} {verdict:>10} ({n*100//CAP}%)")
        results[f"{name}|{kernel}"] = n

with open("/private/tmp/claude-501/-Users-bruce/c853be6a-bb12-4c22-8504-0cc90a372a85/scratchpad/budget_results.json", "w") as f:
    json.dump(results, f, indent=2)
