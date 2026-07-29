"""运行时配置：读写 config.json，缺字段时用默认值，不崩溃。

Phase 3 会把这里扩展成 Web 可编辑的完整 schema（天气城市/股票清单/新闻源）；
Phase 2 目前只需要设备 IP/MAC。
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    "device_ip": "",
    "device_mac": "",
    "divination_pin_minutes": 0,  # 预留字段，当前架构无轮换，暂不生效
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def update(**kwargs):
    cfg = load()
    cfg.update(kwargs)
    save(cfg)
    return cfg
