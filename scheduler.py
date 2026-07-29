"""Phase 7 自动推送调度器：停驻模式下按周期轮换推送。

前提（docs/PHASE0_FINDINGS.md 已实测确认）：设备停在"更换壁纸"界面不退出时，
既保持联网，屏幕又确实显示推送的壁纸内容。所以只要用户把设备就搁在那个
界面上，一个简单的周期性推送就能实现"自动刷新仪表盘"。

默认关闭（未布防），必须用户在设置页显式打开。原因见 ARCHITECTURE.md §3.1：
设备出现的时刻可能是用户自己想用官方页面传图，自动推送会把那次操作覆盖掉。

不用 APScheduler——这里只是"每 N 分钟做一件事、轮换一个列表"，一个后台
daemon 线程 + sleep 循环就够了，不需要额外依赖。
"""
import logging
import threading
from datetime import datetime, timedelta

import config
import device

log = logging.getLogger("pocket-prophet.scheduler")

_thread = None
_stop_event = threading.Event()
_state_lock = threading.Lock()
_state = {
    "armed": False,
    "last_push_at": None,
    "last_push_page": None,
    "last_push_ok": None,
    "last_push_hint": None,
    "next_push_at": None,
}

DISARMED_POLL_SECONDS = 5  # 未布防时多久检查一次"是否被布防了"，让开关能及时生效
MIN_INTERVAL_MINUTES = 5


def get_state() -> dict:
    with _state_lock:
        return dict(_state)


def _next_page(pages: list, last: str) -> str:
    if last in pages:
        i = (pages.index(last) + 1) % len(pages)
    else:
        i = 0
    return pages[i]


def _tick(page_renderers: dict):
    cfg = config.load()
    pages = [p for p in (cfg.get("auto_push_pages") or []) if p in page_renderers]
    ip = cfg.get("device_ip", "")

    if not pages or not ip:
        log.info("自动推送已布防但无可推页面或设备IP未配置，本轮跳过")
        return

    page = _next_page(pages, cfg.get("_auto_push_last_page"))

    try:
        img = page_renderers[page](cfg)
        converted = device.convert(img, kernel="THRESHOLD")
        result = device.push(img, converted["array"], ip)
    except Exception as e:
        result = {"ok": False, "reason": "error", "hint": str(e)}
        log.warning("自动推送 %s 失败: %s", page, e)
    else:
        log.info("自动推送 %s: %s", page, result)

    config.update(_auto_push_last_page=page)
    with _state_lock:
        _state["last_push_at"] = datetime.now().isoformat()
        _state["last_push_page"] = page
        _state["last_push_ok"] = result.get("ok")
        _state["last_push_hint"] = result.get("hint")


def _loop(page_renderers: dict):
    while not _stop_event.is_set():
        cfg = config.load()
        armed = bool(cfg.get("auto_push_enabled"))
        interval_min = max(MIN_INTERVAL_MINUTES, int(cfg.get("auto_push_interval_minutes", 10) or 10))

        with _state_lock:
            _state["armed"] = armed

        if not armed:
            with _state_lock:
                _state["next_push_at"] = None
            _stop_event.wait(DISARMED_POLL_SECONDS)
            continue

        _tick(page_renderers)
        with _state_lock:
            _state["next_push_at"] = (datetime.now() + timedelta(minutes=interval_min)).isoformat()
        _stop_event.wait(interval_min * 60)


def start(page_renderers: dict):
    """启动后台线程。重复调用是安全的（线程已在跑就不重复起）。"""
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_loop, args=(page_renderers,), daemon=True)
    _thread.start()
    log.info("自动推送调度线程已启动（默认未布防，需在设置页开启）")
