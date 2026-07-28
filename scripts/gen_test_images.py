"""Generate test images for reverse-engineering the render/convert API.

Native panel resolution is 200x200 (confirmed via COMPRESS_RENDER preview).
Outputs data-URL-encoded PNGs to out/test_images.json.
"""
import base64
import io
import json
import os
from PIL import Image

W = H = 200
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")


def to_data_url(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/png;base64," + b64


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tests = {}

    for name, gray in [("solid_black", 0), ("solid_g1", 85), ("solid_g2", 170), ("solid_white", 255)]:
        img = Image.new("L", (W, H), gray).convert("RGB")
        tests[name] = to_data_url(img)

    img = Image.new("RGB", (W, H), (255, 255, 255))
    img.putpixel((0, 0), (0, 0, 0))
    tests["marker_topleft"] = to_data_url(img)

    img = Image.new("RGB", (W, H), (255, 255, 255))
    img.putpixel((1, 0), (0, 0, 0))
    tests["marker_x1y0"] = to_data_url(img)

    img = Image.new("RGB", (W, H), (255, 255, 255))
    img.putpixel((0, 1), (0, 0, 0))
    tests["marker_x0y1"] = to_data_url(img)

    img = Image.new("RGB", (W, H))
    px = img.load()
    block = 8
    for x in range(W):
        for y in range(H):
            c = 255 if ((x // block) + (y // block)) % 2 == 0 else 0
            px[x, y] = (c, c, c)
    tests["checker8"] = to_data_url(img)

    out_path = os.path.join(OUT_DIR, "test_images.json")
    with open(out_path, "w") as f:
        json.dump(tests, f)
    print("generated:", list(tests.keys()), "->", out_path)


if __name__ == "__main__":
    main()
