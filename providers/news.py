"""新闻数据源：今日头条热榜公开接口，不需要 API key。

早先考虑过新浪滚动新闻 RSS，实测该源已废弃（整个 feed 只剩一条 2016 年的
视频链接），改用头条热榜——实测确认标题随时间变化、内容时效。
"""
import requests

HOT_BOARD_URL = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
UA = "Mozilla/5.0"
TIMEOUT = 8


def fetch(limit: int = 8) -> list:
    """返回最多 limit 条标题（字符串列表）。"""
    r = requests.get(HOT_BOARD_URL, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json().get("data", [])
    return [item["Title"] for item in data[:limit] if item.get("Title")]
