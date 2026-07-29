"""Claude Code token 消耗：解析本地 JSONL 转录，增量缓存避免每次全量扫描。

**这不是订阅额度百分比** —— 那个数据本地拿不到（ARCHITECTURE.md §4.2 已确认，
`.claude.json` 里没有任何相关缓存）。这里只计算 token 消耗与等价成本估算，
渲染层的文案必须说清楚这一点，不要写成"额度"。

去重键是 `(message.id, requestId)`：实测同一条消息会被写入两次、
token 数完全相同（ARCHITECTURE.md §4.2）。增量解析靠每个文件的读取
偏移量，只对"上次读到哪里之后新增的字节"去重和解析，不会跨次重复计数，
所以不需要一个跨会话持久化的全局去重集合。
"""
import glob
import json
import os
from datetime import datetime, timedelta, timezone

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "ccusage_cache.json")
PRUNE_AFTER_HOURS = 48  # 早于这个窗口的记录对 summarize() 的任何输出都没用

# 近似定价（美元/百万 token），供成本估算用，不代表官方实时价格。
PRICING = {
    "opus": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.5},
    "sonnet": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.3},
    "haiku": {"input": 0.8, "output": 4.0, "cache_write": 1.0, "cache_read": 0.08},
}
DEFAULT_PRICING = PRICING["sonnet"]


def _config_dir() -> str:
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def _pricing_for(model: str) -> dict:
    model_l = (model or "").lower()
    for key, p in PRICING.items():
        if key in model_l:
            return p
    return DEFAULT_PRICING


def _parse_ts(ts_str: str):
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"files": {}, "records": []}


def _save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)


def _parse_new_lines(path: str, offset: int):
    """从 offset 开始读新增内容，返回 (新记录列表, 新 offset)。

    去重只需要在这一次新读到的内容内部做——重复消息实测总是在同一次
    写入里背靠背出现，一旦某段字节被读过并推进了 offset，就不会再被
    读第二次，所以重复项不可能跨两次增量读取分别落在"已读"和"新读"
    两侧。
    """
    records = []
    seen_in_chunk = set()
    with open(path, "rb") as f:
        f.seek(offset)
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not usage:
                continue

            key = (msg.get("id"), d.get("requestId"))
            if key in seen_in_chunk:
                continue
            seen_in_chunk.add(key)

            ts = d.get("timestamp")
            if not ts or not _parse_ts(ts):
                continue

            input_t = usage.get("input_tokens", 0) or 0
            output_t = usage.get("output_tokens", 0) or 0
            cache_w = usage.get("cache_creation_input_tokens", 0) or 0
            cache_r = usage.get("cache_read_input_tokens", 0) or 0
            if input_t + output_t + cache_w + cache_r == 0:
                continue  # 合成/占位消息（如 model="<synthetic>"），跳过

            records.append({
                "ts": ts,
                "model": msg.get("model", "unknown"),
                "input": input_t,
                "output": output_t,
                "cache_write": cache_w,
                "cache_read": cache_r,
            })
        new_offset = f.tell()
    return records, new_offset


def _update_cache() -> dict:
    cache = _load_cache()
    pattern = os.path.join(_config_dir(), "projects", "**", "*.jsonl")
    paths = glob.glob(pattern, recursive=True)

    files_cache = cache.setdefault("files", {})
    records = cache.setdefault("records", [])

    for path in paths:
        try:
            stat = os.stat(path)
        except OSError:
            continue

        entry = files_cache.get(path)
        if entry and entry.get("mtime") == stat.st_mtime and entry.get("offset", 0) >= stat.st_size:
            continue  # 文件没变化

        offset = entry.get("offset", 0) if entry else 0
        if offset > stat.st_size:
            offset = 0  # 文件被截断/替换过，从头读

        new_records, new_offset = _parse_new_lines(path, offset)
        records.extend(new_records)
        files_cache[path] = {"mtime": stat.st_mtime, "offset": new_offset}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=PRUNE_AFTER_HOURS)
    cache["records"] = [r for r in records if (_parse_ts(r["ts"]) or cutoff) >= cutoff]

    _save_cache(cache)
    return cache


def _cost_for(r: dict) -> float:
    p = _pricing_for(r["model"])
    return (
        r["input"] / 1e6 * p["input"]
        + r["output"] / 1e6 * p["output"]
        + r["cache_write"] / 1e6 * p["cache_write"]
        + r["cache_read"] / 1e6 * p["cache_read"]
    )


def summarize() -> dict:
    """返回 {today_tokens, window_5h_tokens, by_model, estimated_cost_usd}。

    `by_model` 和 `estimated_cost_usd` 跟 `today_tokens` 用同一个"今天"边界
    ——这三个数字应该是同一个口径下的今日总量、今日分模型、今日成本，
    不是缓存里整个 48 小时窗口的合计（早先一版写错了，把成本算成了
    48 小时合计却当"今日成本"展示，跟 `ccusage daily` 对不上）。
    """
    cache = _update_cache()

    now = datetime.now(timezone.utc)
    today_start = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = now - timedelta(hours=5)

    today_tokens = 0
    window_tokens = 0
    by_model = {}
    cost = 0.0

    for r in cache["records"]:
        ts = _parse_ts(r["ts"])
        if ts is None:
            continue

        tok = r["input"] + r["output"] + r["cache_write"] + r["cache_read"]

        if ts >= window_start:
            window_tokens += tok

        if ts.astimezone() >= today_start:
            today_tokens += tok
            by_model[r["model"]] = by_model.get(r["model"], 0) + tok
            cost += _cost_for(r)

    return {
        "today_tokens": today_tokens,
        "window_5h_tokens": window_tokens,
        "by_model": by_model,
        "estimated_cost_usd": round(cost, 2),
    }
