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
from providers import qimen as qimen_provider
from providers import stocks as stocks_provider
from providers import weather as weather_provider
from renderer import divination, news, qimen, stocks, usage, weather

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pocket-prophet")

app = Flask(__name__)

def _render_stocks(cfg: dict):
    """行情页有两种版式（Phase 10），在设置页里选：概览（多只）或详情（单只）。"""
    quotes = stocks_provider.fetch(cfg["stock_symbols"])
    if cfg.get("stocks_view") == "detail" and quotes:
        return stocks.render_detail(quotes[0])
    return stocks.render(quotes)


# 配置驱动的内容页：page key -> (中文名, cfg -> PIL.Image)。奇门遁甲仍在
# 这里——自动推送轮换和 /api/preview 还是要用到它的渲染函数——但首页不再
# 走这个表的通用预览/推送 UI，而是跟摇卦一样有自己的独立按钮和结果展示
# （见下方 /api/qimen），因为用户明确要求把它当独立功能对待。摇卦则完全
# 不在这里：它是每次随机的一次性动作，连"轮换推送"都不适用。
PAGES = {
    "weather": ("天气", lambda cfg: weather.render(weather_provider.fetch(cfg["weather_city"]))),
    "stocks": ("行情", _render_stocks),
    "news": ("要闻", lambda cfg: news.render(news_provider.fetch(cfg.get("news_sources")))),
    "usage": ("用量", lambda cfg: usage.render(ccusage.summarize(), cfg.get("usage_daily_budget_tokens"))),
    "qimen": ("奇门遁甲", lambda cfg: qimen.render(qimen_provider.cast())),
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
        "device_ip", "device_mac", "weather_city", "stock_symbols", "stocks_view", "news_sources", "enabled_pages",
        "auto_push_enabled", "auto_push_interval_minutes", "auto_push_pages", "usage_daily_budget_tokens",
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


@app.route("/api/qimen", methods=["POST"])
def api_qimen():
    """奇门遁甲独立入口（首页顶部按钮），跟摇卦同级——用户明确要求把它当
    独立功能提到最上面，而不是塞在通用的预览/推送列表里。跟 /api/divine
    结构一致：起盘 + 转换 + 推送一步到位，返回结构化结果供前端展示。"""
    cfg = config.load()
    ip, info = _resolve_ip(cfg)

    if not ip:
        return jsonify({"ok": False, "reason": "not_configured", "hint": "尚未配置设备 IP"}), 400

    cast = qimen_provider.cast()
    img = qimen.render(cast)

    try:
        converted = device.convert(img, kernel="THRESHOLD")
    except device.ConvertError as e:
        log.warning("转换失败: %s", e)
        return jsonify({"ok": False, "reason": "convert_error", "hint": f"图片转换失败：{e}"}), 502

    push_result = device.push(img, converted["array"], ip)
    preview_b64 = base64.b64encode(converted["render_png"]).decode() if converted["render_png"] else None

    return jsonify({
        "cast": {
            "局": cast["ju"],
            "时柱": cast["shi_zhu"],
            "值符星": cast["zhi_fu_star"],
            "值符宫": cast["zhi_fu_gong"],
        },
        "push": push_result,
        "preview_png_b64": preview_b64,
    })


if __name__ == "__main__":
    scheduler.start({key: fn for key, (_, fn) in PAGES.items()})
    app.run(host="0.0.0.0", port=5151, debug=False)
