"""新闻数据源：多 RSS/Atom 源 + 头条热榜，按用户在设置页配置的清单抓取。

Phase 4 时只有头条热榜；Phase 11 加入通用 RSS/Atom 支持
（providers/rss.py），头条热榜保留为特殊来源——它不是 RSS 接口，用哨兵值
TOUTIAO_SENTINEL 标记。

默认清单（config.py 的 DEFAULTS['news_sources']）里的每个源都逐个实测过：
本项目已经踩过一次坑——新浪滚动新闻 RSS 早已废弃，整个 feed 只剩一条 2016
年的视频链接。这次的默认清单（头条热榜 / solidot / 少数派）全部重新验证
过是活的、有当日/近日条目，不是从网上抄一份清单就直接用。
"""
import requests

from providers import rss as rss_provider

HOT_BOARD_URL = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
UA = "Mozilla/5.0"
TIMEOUT = 8

TOUTIAO_SENTINEL = "toutiao"


def _fetch_toutiao(limit: int) -> list:
    r = requests.get(HOT_BOARD_URL, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json().get("data", [])
    return [item["Title"] for item in data[:limit] if item.get("Title")]


def fetch_source(source: dict, limit: int = 8) -> list:
    """抓单个源。source = {"name": str, "url": str}；url 等于 TOUTIAO_SENTINEL
    时走头条热榜，否则当作 RSS/Atom URL 解析。失败一律返回空列表，不抛
    异常——调用方按清单逐个抓，单个源挂了不该拖累其余源。
    """
    url = source.get("url", "")
    if url == TOUTIAO_SENTINEL:
        try:
            return _fetch_toutiao(limit)
        except (requests.RequestException, ValueError, KeyError):
            return []
    return rss_provider.fetch(url, limit=limit)


def fetch(sources: list = None, limit: int = 8) -> list:
    """按配置的源清单抓取，标题去重后最多返回 limit 条。sources 为空时
    退回头条热榜（兼容 Phase 4 时期只有头条一个源、没有 sources 参数的
    调用方式）。

    合并策略是轮流取（round-robin），不是"排在前面的源先填满"：早期版本
    按清单顺序依次填满，实测发现只要排第一的源自己条目数就够（头条、
    solidot 都轻松≥8条），会导致排在后面的源配了也白配、一条都露不出来，
    "多源"这个功能形同虚设。轮流取才能让清单顺序仍然决定优先级（排前面
    的源循环时先取），但不会让任何一个源独占全部名额。
    """
    if not sources:
        sources = [{"name": "今日头条", "url": TOUTIAO_SENTINEL}]

    per_source = [fetch_source(src, limit=limit) for src in sources]

    seen = set()
    out = []
    idx = [0] * len(per_source)
    while len(out) < limit and any(idx[i] < len(per_source[i]) for i in range(len(per_source))):
        for i, titles in enumerate(per_source):
            if len(out) >= limit:
                break
            while idx[i] < len(titles):
                title = titles[idx[i]]
                idx[i] += 1
                if title not in seen:
                    seen.add(title)
                    out.append(title)
                    break
    return out
