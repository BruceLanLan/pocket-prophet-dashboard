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
    "stocks_view": "overview",  # "overview"(多只概览) 或 "detail"(单只详情，取清单第一只)
    # Phase 11：默认清单，每一条都实测过是活的、有当日/近日条目
    # （教训：新浪滚动新闻 RSS 早已废弃过，见 docs/PLAN-v2.md Phase 11）。
    # 头条放最后：抓取逻辑是"排在前面的源优先填满显示条数"，头条热榜
    # 条目多、几乎总能单独填满全部名额，放第一会让 solidot/少数派配了也
    # 白配、永远露不出来——放最后当兜底，缺口才轮到它补。
    "news_sources": [
        {"name": "奇客Solidot", "url": "https://www.solidot.org/index.rss"},
        {"name": "少数派", "url": "https://sspai.com/feed"},
        {"name": "今日头条", "url": "toutiao"},
    ],
    # Phase 7 自动推送（停驻模式，见 docs/PHASE0_FINDINGS.md）。
    # 默认关闭——必须由用户显式布防，理由见 ARCHITECTURE.md §3.1：
    # 自动推送可能覆盖用户自己用官方页面传图的操作。
    "auto_push_enabled": False,
    "auto_push_interval_minutes": 10,
    "auto_push_pages": ["weather", "stocks", "news", "usage"],  # 不含摇卦，见 PLAN-v2.md Phase 7
    "_auto_push_last_page": None,  # 内部轮换状态，不暴露给设置页
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
