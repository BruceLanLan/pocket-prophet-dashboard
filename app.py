"""最小 Web 服务：摇卦按钮 + 设备在线状态。

docs/PLAN.md Phase 2 步骤 2。绑定 0.0.0.0 以便手机访问局域网内的这台 Mac。
"""
import base64
import logging

from flask import Flask, jsonify, render_template, request

import config
import device
import scheduler
from providers.liuyao import cast_hexagram
from providers import ccusage
from providers import news as news_provider
from providers import stocks as stocks_provider
from providers import weather as weather_provider
from renderer import divination, news, stocks, usage, weather

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pocket-prophet")

app = Flask(__name__)

# 配置驱动的内容页：page key -> (中文名, cfg -> PIL.Image)。摇卦不在这里——
# 它是每次随机的一次性动作，"预览不推送"这个概念对它不适用，走独立的
# /api/divine（见下方，Phase 2 已验证过真机）。
PAGES = {
    "weather": ("天气", lambda cfg: weather.render(weather_provider.fetch(cfg["weather_city"]))),
    "stocks": ("行情", lambda cfg: stocks.render(stocks_provider.fetch(cfg["stock_symbols"]))),
    "news": ("要闻", lambda cfg: news.render(news_provider.fetch())),
    "usage": ("用量", lambda cfg: usage.render(ccusage.summarize())),
}


def _resolve_ip(cfg: dict):
    """按配置的 IP 探活；失败且有 MAC 时按 PLAN.md 的 IP 漂移自愈逻辑找回。"""
    ip = cfg.get("device_ip", "")
    if not ip:
        return None, None

    info = device.info(ip)
    if info is not None:
        return ip, info

    mac = cfg.get("device_mac", "")
    if not mac:
        return ip, None

    new_ip = device.resolve_ip_by_mac(mac)
    if new_ip and new_ip != ip:
        log.info("设备 IP 已漂移: %s -> %s（按 MAC %s 找回）", ip, new_ip, mac)
        config.update(device_ip=new_ip)
        info = device.info(new_ip)
        return new_ip, info

    return ip, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "GET":
        return jsonify(config.load())

    body = request.get_json(force=True, silent=True) or {}
    allowed = {
        "device_ip", "device_mac", "weather_city", "stock_symbols", "news_sources", "enabled_pages",
        "auto_push_enabled", "auto_push_interval_minutes", "auto_push_pages",
    }
    updates = {k: v for k, v in body.items() if k in allowed}
    cfg = config.update(**updates)
    return jsonify(cfg)


@app.route("/api/scheduler_status")
def api_scheduler_status():
    return jsonify(scheduler.get_state())


@app.route("/api/status")
def api_status():
    cfg = config.load()
    ip, info = _resolve_ip(cfg)
    return jsonify({
        "configured": bool(ip),
        "online": info is not None,
        "ip": ip,
        "wallpaper_info": info,
    })


@app.route("/api/pages")
def api_pages():
    return jsonify({key: label for key, (label, _) in PAGES.items()})


@app.route("/api/preview")
def api_preview():
    page = request.args.get("page", "")
    if page not in PAGES:
        return jsonify({"ok": False, "hint": f"未知页面：{page}"}), 404

    cfg = config.load()
    try:
        img = PAGES[page][1](cfg)
    except Exception as e:
        log.warning("渲染 %s 页失败: %s", page, e)
        return jsonify({"ok": False, "hint": f"抓取/渲染失败：{e}"}), 502

    try:
        converted = device.convert(img, kernel="THRESHOLD")
    except device.ConvertError as e:
        return jsonify({"ok": False, "hint": f"图片转换失败：{e}"}), 502

    preview_b64 = base64.b64encode(converted["render_png"]).decode() if converted["render_png"] else None
    return jsonify({"ok": True, "preview_png_b64": preview_b64, "payload_len": len(converted["array"])})


@app.route("/api/push_page", methods=["POST"])
def api_push_page():
    page = request.args.get("page", "")
    if page not in PAGES:
        return jsonify({"ok": False, "hint": f"未知页面：{page}"}), 404

    cfg = config.load()
    ip, _ = _resolve_ip(cfg)
    if not ip:
        return jsonify({"ok": False, "reason": "not_configured", "hint": "尚未配置设备 IP"}), 400

    try:
        img = PAGES[page][1](cfg)
    except Exception as e:
        log.warning("渲染 %s 页失败: %s", page, e)
        return jsonify({"ok": False, "hint": f"抓取/渲染失败：{e}"}), 502

    try:
        converted = device.convert(img, kernel="THRESHOLD")
    except device.ConvertError as e:
        return jsonify({"ok": False, "hint": f"图片转换失败：{e}"}), 502

    push_result = device.push(img, converted["array"], ip)
    preview_b64 = base64.b64encode(converted["render_png"]).decode() if converted["render_png"] else None
    return jsonify({"push": push_result, "preview_png_b64": preview_b64})


@app.route("/api/divine", methods=["POST"])
def api_divine():
    cfg = config.load()
    ip, info = _resolve_ip(cfg)

    if not ip:
        return jsonify({"ok": False, "reason": "not_configured", "hint": "尚未配置设备 IP"}), 400

    cast = cast_hexagram()
    img = divination.render(cast)

    try:
        converted = device.convert(img, kernel="THRESHOLD")
    except device.ConvertError as e:
        log.warning("转换失败: %s", e)
        return jsonify({"ok": False, "reason": "convert_error", "hint": f"图片转换失败：{e}"}), 502

    push_result = device.push(img, converted["array"], ip)

    preview_b64 = base64.b64encode(converted["render_png"]).decode() if converted["render_png"] else None

    return jsonify({
        "cast": {
            "本卦": cast["本卦"],
            "变卦": cast["变卦"],
            "动爻": cast["动爻"],
            "判断": cast["判断"],
        },
        "push": push_result,
        "preview_png_b64": preview_b64,
    })


if __name__ == "__main__":
    scheduler.start({key: fn for key, (_, fn) in PAGES.items()})
    app.run(host="0.0.0.0", port=5151, debug=False)
