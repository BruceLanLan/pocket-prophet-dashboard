"""通用 RSS 2.0 / Atom 解析器，用标准库 xml.etree，不依赖 feedparser
（未安装，且标准库对这两种格式足够用）。

RSS 2.0：<rss><channel><item><title>...
Atom：  <feed xmlns="http://www.w3.org/2005/Atom"><entry><title>...

两种格式的顶层标签名不同（rss vs feed），据此分流解析逻辑。
必须带浏览器 User-Agent——阮一峰博客、solidot 等站点会对无 UA 请求返回 403
（已实测确认，不是这两个源本身有问题）。
"""
import xml.etree.ElementTree as ET

import requests

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 8

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _parse_rss2(root) -> list:
    channel = root.find("channel")
    if channel is None:
        return []
    titles = []
    for item in channel.findall("item"):
        t = item.findtext("title")
        if t:
            titles.append(t.strip())
    return titles


def _parse_atom(root) -> list:
    titles = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        t = entry.findtext(f"{ATOM_NS}title")
        if t:
            titles.append(t.strip())
    return titles


def fetch(url: str, limit: int = 10) -> list:
    """抓一个 RSS/Atom 源，返回标题列表（最多 limit 条）。

    解析失败（网络错误、非法 XML、既不是 rss 也不是 feed 顶层标签）时
    返回空列表而不是抛异常——调用方（providers/news.py）按源逐个抓取，
    单个源失败不该影响其他源。
    """
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except (requests.RequestException, ET.ParseError):
        return []

    tag = root.tag.split("}")[-1]  # 去掉可能的命名空间前缀
    if tag == "rss":
        titles = _parse_rss2(root)
    elif tag == "feed":
        titles = _parse_atom(root)
    else:
        return []

    return titles[:limit]
