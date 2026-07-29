"""天气数据源：wttr.in，免费公开接口，不需要 API key。

数据在用户触发推送时即时抓取，不做预取缓存（PLAN.md 约束 4）。
"""
import requests

WTTR_URL = "https://wttr.in/{city}?format=j1&lang=zh"
TIMEOUT = 8


def fetch(city: str) -> dict:
    """返回 {city, temp_c, desc, humidity, wind_kmph, forecast: [{max_c,min_c}, ...]}"""
    r = requests.get(WTTR_URL.format(city=city), timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json()

    cur = j["current_condition"][0]
    forecast = [
        {"max_c": int(d["maxtempC"]), "min_c": int(d["mintempC"])}
        for d in j["weather"][1:3]  # 明天、后天
    ]

    return {
        "city": city,
        "temp_c": int(cur["temp_C"]),
        "desc": cur["lang_zh"][0]["value"] if cur.get("lang_zh") else cur["weatherDesc"][0]["value"],
        "humidity": int(cur["humidity"]),
        "wind_kmph": int(cur["windspeedKmph"]),
        "forecast": forecast,
    }
