"""设备通信：厂商云端图片转换 + 局域网壁纸推送。

接口契约与所有实测数字见 docs/ARCHITECTURE.md §1、§2。要点：
- 设备大部分时间不可达（§1.5），这是常态不是异常，调用方必须按此设计提示文案
- POST /wallpaper 不可逆，写入前必须先把源图存进 history/
- COMPRESS_ARRAY_V2 是 base64 字符串本身直接当 POST body，不要解码
"""
from __future__ import annotations  # 兼容 Python 3.9：允许用 `dict | None` 写类型注解

import base64
import hashlib
import io
import json
import os
import re
import subprocess
import time
from datetime import datetime

import requests
from PIL import Image

CONVERT_URL = "https://dot.mindreset.tech/api/authV2/device/render/convert"

PROBE_TIMEOUT = 5      # 秒，探活/读状态
PUSH_TIMEOUT = 8       # 秒，写入
CONVERT_TIMEOUT = 25   # 秒，云端转换
CONVERT_RETRIES = 3
CONVERT_BACKOFF_BASE = 1.5  # 秒，指数退避 1.5, 3, 6...

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
STATE_PATH = os.path.join(os.path.dirname(__file__), "state.json")

UNREACHABLE_HINT = "设备当前不在线，请先在设备上打开「更换壁纸」界面"


class ConvertError(Exception):
    """云端转换接口失败（多次重试后仍失败）。"""


def _wallpaper_url(ip: str, path: str = "/wallpaper/info") -> str:
    return f"http://{ip}{path}"


def info(ip: str) -> dict | None:
    """探活并读取设备状态。设备不可达时返回 None，不抛异常。"""
    try:
        r = requests.get(_wallpaper_url(ip), timeout=PROBE_TIMEOUT, proxies={"http": None, "https": None})
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def convert(img: Image.Image, kernel: str = "THRESHOLD") -> dict:
    """调厂商云端转换接口。返回 {"array": COMPRESS_ARRAY_V2字符串, "render_png": bytes预览}。

    失败时指数退避重试 CONVERT_RETRIES 次，全部失败后抛 ConvertError
    （调用方——app.py 的路由——负责转成用户可读的提示，这里保留异常语义
    是因为转换失败原因多样，不像设备不可达那样是单一预期状态）。
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    body = {
        "series": "rand",
        "model": "rand_0",
        "edition": 1,
        "image": data_url,
        "colorLevels": 4,
        "ditherType": "DIFFUSION",
        "ditherKernel": kernel,
    }

    last_err = None
    for attempt in range(CONVERT_RETRIES):
        if attempt > 0:
            time.sleep(CONVERT_BACKOFF_BASE * (2 ** (attempt - 1)))
        try:
            r = requests.post(CONVERT_URL, json=body, timeout=CONVERT_TIMEOUT)
            r.raise_for_status()
            j = r.json()
            array = j.get("COMPRESS_ARRAY_V2")
            if not array:
                raise ConvertError(f"转换接口返回为空: {json.dumps(j)[:200]}")
            render_b64 = j.get("COMPRESS_RENDER")
            render_png = base64.b64decode(render_b64) if render_b64 else None
            return {"array": array, "render_png": render_png}
        except (requests.RequestException, ValueError, ConvertError) as e:
            last_err = e

    raise ConvertError(f"云端转换连续失败 {CONVERT_RETRIES} 次: {last_err}")


def _load_state() -> dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_state(state: dict):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)


def _payload_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def _save_history(img: Image.Image) -> str:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    name = datetime.now().strftime("%Y%m%d-%H%M%S.png")
    path = os.path.join(HISTORY_DIR, name)
    img.save(path)
    return path


def push(img: Image.Image, payload: str, ip: str, force: bool = False) -> dict:
    """推送到设备。永不抛异常，返回结构化结果供路由层直接用于提示文案。

    返回:
      {"ok": True, "skipped": False}                     推送成功
      {"ok": True, "skipped": True, "reason": "unchanged"} 内容未变，跳过
      {"ok": False, "reason": "unreachable", "hint": ...}  设备不可达（常态）
      {"ok": False, "reason": "oversized", "hint": ...}    负载超过 max_upload
      {"ok": False, "reason": "http_error", "hint": ...}   设备返回非 2xx
    """
    state = _load_state()
    dev_info = info(ip)
    if dev_info is None:
        return {"ok": False, "reason": "unreachable", "hint": UNREACHABLE_HINT}

    max_upload = dev_info.get("max_upload", 0)
    if max_upload and len(payload) > max_upload:
        return {
            "ok": False,
            "reason": "oversized",
            "hint": f"图片内容过于复杂（{len(payload)} > {max_upload} 字符），请简化设计",
        }

    h = _payload_hash(payload)
    if not force and state.get("last_pushed_hash") == h:
        return {"ok": True, "skipped": True, "reason": "unchanged"}

    _save_history(img)

    try:
        r = requests.post(
            _wallpaper_url(ip, "/wallpaper"),
            data=payload,
            headers={"Content-Type": "application/octet-stream"},
            timeout=PUSH_TIMEOUT,
            proxies={"http": None, "https": None},
        )
    except requests.RequestException as e:
        return {"ok": False, "reason": "unreachable", "hint": UNREACHABLE_HINT}

    if not r.ok:
        return {
            "ok": False,
            "reason": "http_error",
            "hint": f"设备返回 HTTP {r.status_code}，请重试",
        }

    state["last_pushed_hash"] = h
    state["last_pushed_at"] = datetime.now().isoformat()
    _save_state(state)
    return {"ok": True, "skipped": False}


def render_and_push(img: Image.Image, ip: str, kernel: str = "THRESHOLD", force: bool = False) -> dict:
    """便捷封装：转换 + 推送一步到位，供 app.py 路由直接调用。"""
    try:
        converted = convert(img, kernel=kernel)
    except ConvertError as e:
        return {"ok": False, "reason": "convert_error", "hint": f"图片转换失败：{e}"}
    return push(img, converted["array"], ip, force=force)


_MAC_RE = re.compile(r"\(([\d.]+)\) at ([0-9a-f]{1,2}(?::[0-9a-f]{1,2}){5})", re.IGNORECASE)


def resolve_ip_by_mac(mac: str) -> str | None:
    """扫本机 ARP 表找 MAC 对应的当前 IP（IP 漂移自愈，见 PLAN.md Phase 1）。"""
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    mac_norm = mac.lower()
    for m in _MAC_RE.finditer(out):
        ip, found_mac = m.group(1), m.group(2).lower()
        # arp -a 里单字节可能省略前导0（如 0a 写作 a），标准化后再比较
        found_norm = ":".join(p.zfill(2) for p in found_mac.split(":"))
        want_norm = ":".join(p.zfill(2) for p in mac_norm.split(":"))
        if found_norm == want_norm:
            return ip
    return None
