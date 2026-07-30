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
    # 抓取是轮流取（round-robin），顺序决定的是"每一轮谁先取、余数给谁"，
    # 不是"谁能把名额占满"（早期版本是顺序填满，头条/solidot 随便一个
    # 排第一都会把另外两个源直接挤没，已改掉，见 providers/news.py）。
    # 头条放最后，把余数留给它兜底，前两个更有内容深度的源优先露出。
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
    # Phase 12：用户自设的每日 token 预算，不是官方额度（本地拿不到，
    # 见 ARCHITECTURE.md §4.2）。渲染时必须把这个数字本身也画出来，
    # 让人一眼看出百分比是相对这个自设基准算的，不是官方口径。
    "usage_daily_budget_tokens": 200_000_000,
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
