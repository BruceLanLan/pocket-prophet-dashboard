"""行情数据源：Yahoo Finance 公开 chart 接口，不需要 API key。

必须带浏览器 User-Agent，否则会被拒绝（已实测：不带 UA 返回 429）。

下次财报日期本想一并加（docs/PLAN-v2.md Phase 10），但那需要
v10/finance/quoteSummary 接口，实测无认证访问返回 401 Unauthorized/
Invalid Crumb——不去处理认证绕过，按计划里"若接口可得"的但书直接跳过。
"""
import requests

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
TIMEOUT = 8


def _fetch_one(symbol: str) -> dict:
    r = requests.get(
        CHART_URL.format(symbol=symbol),
        params={"range": "1d", "interval": "15m"},
        headers={"User-Agent": UA},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    result = r.json()["chart"]["result"][0]
    meta = result["meta"]

    price = meta["regularMarketPrice"]
    prev_close = meta["previousClose"]
    change_pct = (price - prev_close) / prev_close * 100 if prev_close else 0.0

    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    closes = [c for c in closes if c is not None]

    return {
        "symbol": symbol,
        "name": meta.get("shortName", symbol),
        "price": price,
        "change_pct": change_pct,
        "closes": closes,
        "volume": meta.get("regularMarketVolume"),
        "week52_high": meta.get("fiftyTwoWeekHigh"),
        "week52_low": meta.get("fiftyTwoWeekLow"),
    }


def fetch(symbols: list) -> list:
    """按清单逐个拉取，单个标的失败不影响其余（返回里跳过失败项）。"""
    out = []
    for s in symbols:
        try:
            out.append(_fetch_one(s))
        except (requests.RequestException, KeyError, IndexError, ValueError):
            continue
    return out
