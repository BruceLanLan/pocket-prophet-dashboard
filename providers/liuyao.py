"""六爻起卦：三枚铜钱法，六次抛掷。

用 `secrets` 而非 `random`（docs/PLAN.md Phase 2 约束）。

三钱法：每枚铜钱取 2（字/阴面）或 3（背/阳面），三枚求和，
和值 6/7/8/9 分别对应 老阴/少阳/少阴/老阳 —— 这是通行的标准映射，
参见任何六爻入门资料，不是本项目自定义的。
老阴、老阳为"动爻"：变卦中会翻转为对立的阴阳。
"""
import secrets

from providers.hexagram_tables import BA_GUA_NUM, GUA_READING, HEXAGRAM_NAMES

# 三爻位 -> 八卦，(下,中,上) 三个爻的阴阳，1=阳(实线) 0=阴(断线)
TRIGRAM_BITS = {
    "乾": (1, 1, 1),
    "兑": (1, 1, 0),
    "离": (1, 0, 1),
    "震": (1, 0, 0),
    "巽": (0, 1, 1),
    "坎": (0, 1, 0),
    "艮": (0, 0, 1),
    "坤": (0, 0, 0),
}
BITS_TO_TRIGRAM = {v: k for k, v in TRIGRAM_BITS.items()}

# 和值 -> (爻名, 当前是否为阳, 是否为动爻)
LINE_TYPES = {
    6: ("老阴", False, True),
    7: ("少阳", True, False),
    8: ("少阴", False, False),
    9: ("老阳", True, True),
}


def _toss_coin() -> int:
    """单枚铜钱：2（字/阴）或 3（背/阳），等概率。"""
    return secrets.choice((2, 3))


def cast_line() -> int:
    """抛三枚铜钱求和，返回 6/7/8/9。"""
    return sum(_toss_coin() for _ in range(3))


def _trigram_name(bits3):
    return BITS_TO_TRIGRAM[tuple(bits3)]


def _hexagram_name(bits6):
    """bits6: 长度 6 的 0/1 元组，索引 0 是初爻（最下）。"""
    lower = _trigram_name(bits6[0:3])
    upper = _trigram_name(bits6[3:6])
    return HEXAGRAM_NAMES[(BA_GUA_NUM[upper], BA_GUA_NUM[lower])], upper, lower


def cast_hexagram() -> dict:
    """起一卦：六次抛掷，返回本卦/变卦/动爻等完整信息。

    lines: 长度 6 的列表，索引 0 是初爻（最下），元素为 (sum, name, is_yang, is_changing)
    """
    lines = []
    for _ in range(6):
        s = cast_line()
        name, is_yang, is_changing = LINE_TYPES[s]
        lines.append({"sum": s, "name": name, "is_yang": is_yang, "is_changing": is_changing})

    current_bits = tuple(1 if l["is_yang"] else 0 for l in lines)
    changed_bits = tuple(
        (1 - b) if l["is_changing"] else b
        for b, l in zip(current_bits, lines)
    )

    hex_name, upper, lower = _hexagram_name(current_bits)
    moving_positions = [i + 1 for i, l in enumerate(lines) if l["is_changing"]]  # 1=初爻...6=上爻

    result = {
        "lines": lines,  # 初爻 -> 上爻
        "本卦": hex_name,
        "本卦_上": upper,
        "本卦_下": lower,
        "动爻": moving_positions,
        "判断": GUA_READING.get(hex_name, ""),
    }

    if moving_positions:
        chg_hex_name, chg_upper, chg_lower = _hexagram_name(changed_bits)
        result["变卦"] = chg_hex_name
        result["变卦_上"] = chg_upper
        result["变卦_下"] = chg_lower
    else:
        # 六爻皆不动（无老阴老阳），传统上无变卦，以本卦断
        result["变卦"] = None
        result["变卦_上"] = None
        result["变卦_下"] = None

    return result
