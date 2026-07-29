"""运行时配置：读写 config.json，缺字段时用默认值，不崩溃。

Phase 3 schema。天气城市/股票清单/新闻源目前只是数据模型（Phase 4 才会
真正消费它们），但设备 IP/MAC/启用页面现在就是完整可用的。
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    "device_ip": "",
    "device_mac": "",
    "enabled_pages": ["divination"],  # Phase 4/5 陆续加入 weather/stocks/news/usage
    "weather_city": "深圳",
    "stock_symbols": ["AAPL", "NVDA"],  # 用户 2026-07-28 确认的初始清单
    "news_sources": [],  # Phase 4 实现 providers/news.py 时补默认源
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
