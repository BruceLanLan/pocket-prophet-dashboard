"""Call the vendor's render/convert API for each test image and inspect the result.

Reads out/test_images.json (see gen_test_images.py), writes out/full_arrays.json
with the raw COMPRESS_ARRAY_V2 payloads for offline analysis.
"""
import json
import os
import requests

CONVERT_URL = "https://dot.mindreset.tech/api/authV2/device/render/convert"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")


def main():
    with open(os.path.join(OUT_DIR, "test_images.json")) as f:
        tests = json.load(f)

    full = {}
    for name, data_url in tests.items():
        body = {
            "series": "rand",
            "model": "rand_0",
            "edition": 1,
            "image": data_url,
            "colorLevels": 4,
            "ditherType": "DIFFUSION",
            "ditherKernel": "THRESHOLD",
        }
        r = requests.post(CONVERT_URL, json=body, timeout=25)
        j = r.json()
        arr = j.get("COMPRESS_ARRAY_V2", "")
        full[name] = arr
        print(name, "->", r.status_code, "base64_len=", len(arr))

    with open(os.path.join(OUT_DIR, "full_arrays.json"), "w") as f:
        json.dump(full, f)


if __name__ == "__main__":
    main()
