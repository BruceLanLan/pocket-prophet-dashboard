"""奇门遁甲起盘：包装 qimen_engine.py，按当前时间起盘，输出渲染层需要的扁平结构。

排盘逻辑完全来自引擎本身（节气定局/阴阳遁/值符值使/三盘），这里只做两件事：
按当前时间转四柱、把引擎输出整理成渲染器容易消费的形状。

中宫（5号宫）处理：引擎的 `宫位详情` 字典本身就没有 5 号键——中宫没有自己的
八门/八神，其内容按传统"寄某宫"的规则并入另一个宫（该宫数据里会带
`中宫寄: true` 标记）。这是引擎自己的规则，这里不重新实现，只是在渲染时
中间那格用 `中宫处理` 里的九星信息单独显示，不套用寻常宫格的模板。
"""
import datetime

from providers import qimen_engine as qe

# 3x3 屏幕网格的宫位号排列（洛书方位，传统奇门盘的标准摆法）：
# 巽4 离9 坤2
# 震3 中5 兑7
# 艮8 坎1 乾6
GRID_LAYOUT = [4, 9, 2, 3, 5, 7, 8, 1, 6]


def cast(dt=None) -> dict:
    """起一盘。dt 为空则用当前时间。"""
    dt = dt or datetime.datetime.now()
    pillars, date_tuple = qe.datetime_to_question_pillars(dt)
    result = qe.pai_full(pillars, date_tuple)

    gong_detail = result["宫位详情"]
    zhong = result["中宫处理"]

    cells = []
    for gong_num in GRID_LAYOUT:
        if gong_num == 5:
            cells.append({
                "gong_num": 5,
                "is_zhong": True,
                "star": zhong["jiu_xing"]["star"],
                "note": zhong.get("zhong_gong_note", ""),
            })
            continue

        g = gong_detail[gong_num]
        cells.append({
            "gong_num": gong_num,
            "is_zhong": False,
            "direction": g["方位"],
            "men": g["八门"],
            "star": g["九星"],
            "shen": g["八神"],
            "di_gan": g["地盘"],
            "tian_gan": g["天盘"],
            "is_zhi_fu": gong_num == result["值符宫"],
        })

    return {
        "dt": dt,
        "ju": result["局"],
        "shi_zhu": result["时柱"],
        "zhi_fu_star": result["值符星"],
        "zhi_fu_gong": result["值符宫"],
        "cells": cells,
    }
