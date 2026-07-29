"""天气数据源：wttr.in，免费公开接口，不需要 API key。

数据在用户触发推送时即时抓取，不做预取缓存（PLAN.md 约束 4）。
"""
import requests

WTTR_URL = "https://wttr.in/{city}?format=j1&lang=zh"
TIMEOUT = 8


def fetch(city: str) -> dict:
    """返回 {city, temp_c, feels_like_c, desc, code, humidity, wind_kmph,
    chance_of_rain, forecast: [{max_c,min_c}, ...]}"""
    r = requests.get(WTTR_URL.format(city=city), timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json()

    cur = j["current_condition"][0]
    today_hourly = j["weather"][0]["hourly"]
    forecast = [
        {"max_c": int(d["maxtempC"]), "min_c": int(d["mintempC"])}
        for d in j["weather"][1:3]  # 明天、后天
    ]

    return {
        "city": city,
        "temp_c": int(cur["temp_C"]),
        "feels_like_c": int(cur["FeelsLikeC"]),
        "desc": cur["lang_zh"][0]["value"] if cur.get("lang_zh") else cur["weatherDesc"][0]["value"],
        "code": cur["weatherCode"],  # worldweatheronline 天气代码，见 renderer/weather_icons.py
        "humidity": int(cur["humidity"]),
        "wind_kmph": int(cur["windspeedKmph"]),
        "chance_of_rain": max((int(h.get("chanceofrain", 0)) for h in today_hourly), default=0),
        "forecast": forecast,
    }
