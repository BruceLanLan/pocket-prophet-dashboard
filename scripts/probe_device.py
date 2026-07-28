"""Query a Pocket Prophet (口袋先知) device's local wallpaper endpoint.

Usage:
    python3 probe_device.py <device-ip>
"""
import sys
import json
import urllib.request


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    ip = sys.argv[1]
    url = f"http://{ip}/wallpaper/info"
    with urllib.request.urlopen(url, timeout=5) as r:
        info = json.loads(r.read())
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
