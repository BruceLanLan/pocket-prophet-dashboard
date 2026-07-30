# -*- coding: utf-8 -*-
"""
奇门遁甲排盘引擎 v2.0 — 九星 / 八神 / 八门 / 三盘 / 终身局 / 财富信号
#[v2.0] 完全重写版

原样复制自同一作者的另一个命理相关项目。整份复制而非跨仓库引用一个
只在开发机上存在的绝对路径，是为了让 pocket-prophet-dashboard 能被
独立 clone、独立跑起来（README 的前提）。
"""

import math
from typing import Dict, List, Optional, Tuple, Any

# ── 基础数据 ────────────────────────────────────────────────

TIAN_GAN = '甲乙丙丁戊己庚辛壬癸'
DI_ZHI = '子丑寅卯辰巳午未申酉戌亥'
SHI_CHEN = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 九宫: 洛书数 → 八卦方位
GONG_MAP = {1:'坎',2:'坤',3:'震',4:'巽',5:'中',6:'乾',7:'兑',8:'艮',9:'离'}
GONG_WUXING = {1:'水',2:'土',3:'木',4:'木',5:'土',6:'金',7:'金',8:'土',9:'火'}
GONG_CAIWEI = {8:'财帛宫(艮)',4:'财帛宫(巽)',9:'财帛宫(离)'}  # 财帛相关宫位

# 八门
MEN_NAMES = ['休','死','伤','杜','开','惊','生','景']
MEN_GONG = {'休':1,'死':2,'伤':3,'杜':4,'开':6,'惊':7,'生':8,'景':9}
MEN_WUXING = {'休':'水','死':'土','伤':'木','杜':'木','开':'金','惊':'金','生':'土','景':'火'}
MEN_MEANING = {
    '休':'休养生息,宜静不宜动',
    '生':'生机勃勃,财运亨通',
    '伤':'损伤破财,谨慎行事',
    '杜':'堵塞不通,宜守不宜攻',
    '景':'虚幻美景,看破放下',
    '死':'死寂绝望,绝处逢生',
    '惊':'惊恐不安,谨言慎行',
    '开':'开创通达,万事大吉',
}
MEN_JIXIONG = {
    '休':'大吉','生':'大吉','开':'大吉',
    '景':'平','杜':'平',
    '伤':'凶','惊':'凶','死':'大凶',
}

# 九星
STAR_NAMES = ['天蓬','天芮','天冲','天辅','天禽','天心','天柱','天任','天英']
STAR_GONG = {'天蓬':1,'天芮':2,'天冲':3,'天辅':4,'天禽':5,'天心':6,'天柱':7,'天任':8,'天英':9}
STAR_WUXING = {'天蓬':'水','天芮':'土','天冲':'木','天辅':'木','天禽':'土','天心':'金','天柱':'金','天任':'土','天英':'火'}
STAR_MEANING = {
    '天蓬':'大胆冒险,水星。春夏可用,秋冬不可用',
    '天芮':'病符,土星。宜授道结交',
    '天冲':'冲锋,木星。出军报仇雪耻',
    '天辅':'文曲,木星。大吉,远行修造',
    '天禽':'中正,土星。大吉,远行经商',
    '天心':'周密,金星。求仙合药,经商迁徙',
    '天柱':'顶梁,金星。宜隐迹固守',
    '天任':'负荷,土星。小吉,求官嫁娶',
    '天英':'光华,火星。百事不宜',
}
STAR_JIXIONG = {
    '天辅':'大吉','天禽':'大吉','天心':'大吉',
    '天任':'小吉','天冲':'小吉',
    '天柱':'小凶','天英':'小凶',
    '天蓬':'大凶','天芮':'大凶',
}

# 八神 (固定顺序)
SHEN_NAMES = ['值符','腾蛇','太阴','六合','白虎','玄武','九地','九天']
SHEN_MEANING = {
    '值符':'诸神之首,百恶消散',
    '腾蛇':'虚诈之神,惊恐怪异',
    '太阴':'荫佑之神,宜闭城藏兵',
    '六合':'护卫之神,宜婚姻交易',
    '白虎':'凶恶之神,兵戈争斗',
    '玄武':'奸谗小盗之神',
    '九地':'坚牢之神,宜屯兵固守',
    '九天':'威悍之神,宜扬兵布阵',
}

# 六甲旬首 → 隐藏六仪
XUN_SHOU = {
    '甲子':'戊','甲戌':'己','甲申':'庚','甲午':'辛','甲辰':'壬','甲寅':'癸',
}

# 六仪三奇顺序 (阳遁顺排, 阴遁逆排)
YI_QI_SHUN = ['戊','己','庚','辛','壬','癸','丁','丙','乙']

# 旬首→值符星索引 (0=天蓬)
XUN_TO_STAR_IDX = {
    '甲子':0, '甲戌':1, '甲申':2, '甲午':3, '甲辰':4, '甲寅':5,
}

# 干支索引映射
TIAN_GAN_IDX = {g:i for i,g in enumerate(TIAN_GAN)}
DI_ZHI_IDX = {z:i for i,z in enumerate(DI_ZHI)}

# 阴遁日支集合
YIN_ZHI_SET = {'巳','午','未','申','酉','戌'}
YANG_ZHI_SET = {'亥','子','丑','寅','卯','辰'}

# 日干→局数 (简化映射)
GAN_JU_MAP = {'甲':3,'乙':8,'丙':9,'丁':7,'戊':5,'己':2,'庚':1,'辛':4,'壬':6,'癸':7}

# 阳遁局数表 (节气 → 上中下三元局数)
# Q0: 与 knowledge/qimen/1-foundation.md §2.3 定局合同一致（禁自创表）
YANG_DUN = {
    '冬至': (1, 7, 4), '惊蛰': (1, 7, 4),
    '小寒': (2, 8, 5), '立春': (2, 8, 5),
    '大寒': (3, 9, 6), '春分': (3, 9, 6),
    '雨水': (9, 6, 3), '清明': (9, 6, 3),
    '立夏': (4, 1, 7), '谷雨': (4, 1, 7),
    '小满': (5, 2, 8), '芒种': (5, 2, 8),
}
# 阴遁局数表 — 同上 KB 合同
YIN_DUN = {
    '夏至': (9, 3, 6), '白露': (9, 3, 6),
    '小暑': (8, 2, 5), '立秋': (8, 2, 5),
    '大暑': (7, 1, 4), '秋分': (7, 1, 4),
    '处暑': (1, 4, 7), '寒露': (1, 4, 7),
    '立冬': (6, 9, 3), '霜降': (6, 9, 3),
    '小雪': (5, 8, 2), '大雪': (5, 8, 2),
}

# Q0 定局合同快照（测试/断言用；须与 YANG_DUN/YIN_DUN 恒等）
DINGJU_KB_YANG = dict(YANG_DUN)
DINGJU_KB_YIN = dict(YIN_DUN)

NON_QUESTION_CHART_LABEL = '非问事时盘'
QUESTION_CHART_LABEL = '问事时盘'
REFUSE_NO_DATETIME = '无问事 datetime：奇门为问事时盘，拒答。'
# 节气列表 (名称,月,日) 用于定局计算  #[v2.1]
JIEQI_LIST = [
    ('小寒',1,6), ('大寒',1,20),
    ('立春',2,4), ('雨水',2,19),
    ('惊蛰',3,6), ('春分',3,21),
    ('清明',4,5), ('谷雨',4,20),
    ('立夏',5,6), ('小满',5,21),
    ('芒种',6,6), ('夏至',6,21),
    ('小暑',7,7), ('大暑',7,23),
    ('立秋',8,7), ('处暑',8,23),
    ('白露',9,8), ('秋分',9,23),
    ('寒露',10,8), ('霜降',10,23),
    ('立冬',11,7), ('小雪',11,22),
    ('大雪',12,7), ('冬至',12,22),
]

# 用神配置表  #[v2.1 / Q0]
# reference_gong = 学理参考宫（如财帛艮），≠ 盘上符号实落宫；实落由 locate 算出。
YONG_SHEN_CONFIG = {
    'wealth': {
        'men': '生', 'gan': '戊', 'reference_gong': 8, 'gong': 8,
        'description': '求财以生门为用神,戊为财星；落宫=生门实落（参考财帛艮）',
    },
    'career': {
        'men': '开', 'gan': '丁', 'reference_gong': 6, 'gong': 6,
        'description': '事业以开门为用神,丁为官星；落宫=开门实落（参考乾）',
    },
    'love': {
        'men': '休', 'gan': '乙', 'reference_gong': 6, 'gong': 6,
        'description': '感情以休门/乙为用神；落宫=休门或乙实落（参考乾）',
    },
    'health': {
        'men': '死', 'gan': '戊', 'reference_gong': 2, 'gong': 2,
        'description': '健康以死门为用神；落宫=死门实落（参考坤病符）',
    },
    'general': {
        'men': '休', 'gan': '甲', 'reference_gong': 1, 'gong': 1,
        'description': '通用以休门为用神；落宫=休门实落（参考坎）',
    },
}

# ── 辅助函数 ────────────────────────────────────────────────

#[v2.0]
def _parse_bazi(bazi_str: str) -> Optional[Tuple[str, str, str, str]]:
    """解析八字四柱 '甲子 乙丑 丙寅 丁卯' → (年柱,月柱,日柱,时柱)
    支持紧凑格式 '甲子乙丑丙寅丁卯' (8字符无空格)"""
    s = bazi_str.strip()
    parts = s.split()
    if len(parts) < 4:
        import re
        parts = re.split(r'[\s,，、]+', s)
    if len(parts) < 4:
        # 紧凑8字符格式: '甲子乙丑丙寅丁卯'
        if len(s) == 8:
            parts = [s[i:i+2] for i in range(0, 8, 2)]
    if len(parts) < 4:
        return None
    return parts[0], parts[1], parts[2], parts[3]

#[v2.3]
def _get_xun(ggan: str, gzhi: str) -> str:
    """根据天干地支获取旬首名称, e.g. ('甲','子') → '甲子'
    算法: 先计算六十花甲子序号k, 然后旬首 = k // 10 * 10 位置的干支
    """
    if ggan not in TIAN_GAN_IDX or gzhi not in DI_ZHI_IDX:
        return '甲子'
    n = TIAN_GAN_IDX[ggan]
    m = DI_ZHI_IDX[gzhi]
    # 六十花甲子序号k (0~59): k%10=n, k%12=m
    # k = m + 12 * p, 其中 p = ((n-m)/2) mod 5
    diff = (n - m) % 10
    p = diff // 2
    k = m + 12 * p
    # 旬首 = 该旬的第一个干支 (天干一定是甲)
    xun_start = (k // 10) * 10
    xun_zhi = DI_ZHI[xun_start % 12]
    return '甲' + xun_zhi

#[v2.0]
def _get_xun_tiangan(xun_name: str) -> str:
    """旬首名称 → 六仪天干, e.g. '甲子' → '戊'"""
    return XUN_SHOU.get(xun_name, '戊')

#[v2.0]
def _get_ju_from_gan(day_gan: str) -> int:
    """基于日干获取局数 (v2.1后用于fallback)"""
    return GAN_JU_MAP.get(day_gan, 5)

#[v2.2]
def _get_ju_from_jieqi(year: int, month: int, day: int) -> Tuple[int, str]:
    """
    节气定局 v2.2 (三元定局)
    根据公历日期计算节气区间和上中下元,确定阴阳遁和局数
    返回: (局数, 阴阳遁)
    阳遁: 冬至→芒种, 阴遁: 夏至→大雪
    上中下元: 每元5天, 根据节气内偏移量计算
    """
    try:
        date_val = month * 100 + day
        from datetime import date as dt_date

        # 找到当前日期所在的节气区间
        current_jieqi = None
        for i, (name, m, d) in enumerate(JIEQI_LIST):
            jieqi_val = m * 100 + d
            if date_val < jieqi_val:
                if i == 0:
                    current_jieqi = ('冬至', 12, 22)
                else:
                    current_jieqi = JIEQI_LIST[i - 1]
                break
        else:
            current_jieqi = JIEQI_LIST[-1]

        jieqi_name = current_jieqi[0]
        jieqi_m, jieqi_d = current_jieqi[1], current_jieqi[2]

        # 计算节气日期 (冬至跨年时用前一年)
        jieqi_year = year
        if jieqi_name == '冬至' and month <= 1 and day <= 5:
            jieqi_year = year - 1
        jieqi_date_obj = dt_date(jieqi_year, jieqi_m, jieqi_d)
        cur_date_obj = dt_date(year, month, day)
        days_diff = (cur_date_obj - jieqi_date_obj).days
        if days_diff < 0:
            days_diff += 15

        # 三元: 每元5天, 上中下轮转
        yuan_names = ['上元', '中元', '下元']
        yuan_idx = (days_diff // 5) % 3

        # 查局数表
        if jieqi_name in YANG_DUN:
            ju_nums = YANG_DUN[jieqi_name]
            yin_yang = '阳'
        elif jieqi_name in YIN_DUN:
            ju_nums = YIN_DUN[jieqi_name]
            yin_yang = '阴'
        else:
            return _get_ju_from_gan('甲'), '阳'

        ju = ju_nums[yuan_idx]
        return ju, yin_yang

    except Exception:
        return _get_ju_from_gan('甲'), '阳'


#[v2.1]
def _handle_zhong_gong(gong_map: Dict[int, Dict]) -> Dict[int, Dict]:
    """
    中宫处理 #[v2.1]
    天禽星坐中宫,寄坤宫(2)但保留中宫信息
    返回更新后的gong_map,包含中宫标志
    """
    try:
        result = dict(gong_map)

        # 检查中宫(5)是否有数据
        if 5 in result:
            zhong_info = result[5]
            # 坤宫(2)标记中宫寄宫信息
            if 2 in result:
                result[2]['zhong_gong'] = True
                result[2]['zhong_gong_info'] = dict(zhong_info)
                result[2]['zhong_gong_note'] = '中宫天禽寄此'

            # 保留中宫标记
            result[5]['is_zhong_gong'] = True
            result[5]['zhong_gong_note'] = '天禽坐中,寄坤'

        return result

    except Exception:
        return gong_map


def assert_dingju_matches_kb() -> None:
    """Q0: 引擎定局表必须与 KB foundation §2.3 合同恒等。"""
    if YANG_DUN != DINGJU_KB_YANG:
        raise AssertionError(f'YANG_DUN 偏离 KB 合同: {YANG_DUN!r} vs {DINGJU_KB_YANG!r}')
    if YIN_DUN != DINGJU_KB_YIN:
        raise AssertionError(f'YIN_DUN 偏离 KB 合同: {YIN_DUN!r} vs {DINGJU_KB_YIN!r}')
    # 关键冲突点：曾与 KB 不一致的节气
    assert YANG_DUN['立春'] == (2, 8, 5)
    assert YANG_DUN['清明'] == (9, 6, 3)
    assert YANG_DUN['谷雨'] == (4, 1, 7)
    assert YANG_DUN['芒种'] == (5, 2, 8)
    assert YIN_DUN['立秋'] == (8, 2, 5)
    assert YIN_DUN['寒露'] == (1, 4, 7)
    assert YIN_DUN['霜降'] == (6, 9, 3)
    assert YIN_DUN['大雪'] == (5, 8, 2)


def locate_yong_shen_gong(
    gong_details: Dict[int, Dict],
    *,
    men: Optional[str] = None,
    gan: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Q0: 用神落宫 = 符号在盘上的实落，禁止固定读参考宫。
    优先人盘八门；其次天盘干；再次地盘干。
    """
    men_gong = None
    gan_gong_tian = None
    gan_gong_di = None
    for g, info in (gong_details or {}).items():
        if men and men_gong is None and info.get('八门') == men:
            men_gong = int(g)
        if gan:
            if gan_gong_tian is None and info.get('天盘') == gan:
                gan_gong_tian = int(g)
            if gan_gong_di is None and info.get('地盘') == gan:
                gan_gong_di = int(g)
    # 落宫语义：问事看用神之门实落；无门则看干实落
    primary = men_gong if men_gong is not None else (gan_gong_tian or gan_gong_di)
    return {
        'gong': primary,
        'men_gong': men_gong,
        'gan_gong_tian': gan_gong_tian,
        'gan_gong_di': gan_gong_di,
        'by': 'men' if men_gong is not None else ('gan_tian' if gan_gong_tian else ('gan_di' if gan_gong_di else None)),
    }


#[v2.1]
def _get_yong_shen(bazi: Tuple[str, str, str, str],
                   question_type: str = 'wealth') -> Dict[str, Any]:
    """
    用神体系 #[v2.1 / Q0]
    返回符号（门/干）与参考宫；实落宫须在排盘后由 locate_yong_shen_gong 写入。
    """
    try:
        config = YONG_SHEN_CONFIG.get(question_type, YONG_SHEN_CONFIG['general'])
        ref = config.get('reference_gong', config.get('gong', 1))

        result = {
            'yong_shen_men': config['men'],
            'yong_shen_gan': config['gan'],
            # 兼容旧键：暂填参考宫；analyze 会覆写为符号实落
            'yong_shen_gong': ref,
            'yong_shen_reference_gong': ref,
            'yong_shen_description': config['description'],
            'question_type': question_type,
        }

        # 感情类特殊处理: 加入庚(男方)信息
        if question_type == 'love' and bazi:
            result['yong_shen_gan_female'] = '乙'
            result['yong_shen_gan_male'] = '庚'

        return result

    except Exception:
        return {
            'yong_shen_men': '休',
            'yong_shen_gan': '甲',
            'yong_shen_gong': 1,
            'yong_shen_reference_gong': 1,
            'yong_shen_description': '通用用神',
            'question_type': question_type,
        }


# ── Q0: 问事 datetime → 日时柱 ──────────────────────────────

_Q0_GAN = list(TIAN_GAN)
_Q0_ZHI = list(DI_ZHI)


def _q0_day_pillar(year: int, month: int, day: int) -> str:
    """公历日 → 日柱（与 validate_hf_bazi 同锚：1900-01-01=甲戌）。"""
    from datetime import date as dt_date
    ref = dt_date(1900, 1, 1)
    ref_idx = 10  # 甲戌
    delta = (dt_date(year, month, day) - ref).days
    idx = (ref_idx + delta) % 60
    return _Q0_GAN[idx % 10] + _Q0_ZHI[idx % 12]


def _q0_hour_pillar(day_gan: str, hour: float) -> str:
    """时柱：日干起时 + 时辰地支。"""
    shichen = int((hour + 1) // 2) % 12
    day_gan_idx = _Q0_GAN.index(day_gan)
    start_gan_idx = (day_gan_idx % 5) * 2
    gan_idx = (start_gan_idx + shichen) % 10
    return _Q0_GAN[gan_idx] + _Q0_ZHI[shichen]


def datetime_to_question_pillars(question_dt) -> Tuple[str, Tuple[int, int, int]]:
    """
    问事 datetime → (四柱字符串, date_tuple)。
    年/月柱用简化立春/节气边界；奇门起局关键取日时柱 + 节气定局。
    """
    from datetime import datetime as dt_cls, date as dt_date, timedelta
    if not isinstance(question_dt, dt_cls):
        raise TypeError('question_dt 须为 datetime')
    year, month, day = question_dt.year, question_dt.month, question_dt.day
    hour = question_dt.hour + question_dt.minute / 60.0

    # 年柱（立春 2/4 界）
    y = year - 1 if (month < 2 or (month == 2 and day < 4)) else year
    y_idx = (y - 4) % 60
    year_pillar = _Q0_GAN[y_idx % 10] + _Q0_ZHI[y_idx % 12]

    # 月柱（节令粗边界，与 validate_hf_bazi 一致）
    dt = dt_date(year, month, day)
    prev = year - 1
    boundaries = [
        (prev, 11, 7, 9), (prev, 12, 7, 10),
        (year, 1, 6, 11), (year, 2, 4, 0), (year, 3, 6, 1),
        (year, 4, 5, 2), (year, 5, 5, 3), (year, 6, 6, 4),
        (year, 7, 7, 5), (year, 8, 7, 6), (year, 9, 8, 7),
        (year, 10, 8, 8), (year, 11, 7, 9), (year, 12, 7, 10),
    ]
    solar_month = 11
    for by, bm, bd, month_idx in reversed(boundaries):
        if dt >= dt_date(by, bm, bd):
            solar_month = month_idx
            break
    start_gan_idx = _Q0_GAN.index(year_pillar[0])
    month_start_gan = (start_gan_idx % 5) * 2 + 2
    month_pillar = (
        _Q0_GAN[(month_start_gan + solar_month) % 10]
        + _Q0_ZHI[(solar_month + 2) % 12]
    )

    day_pillar = _q0_day_pillar(year, month, day)
    if hour >= 23:
        next_day = question_dt + timedelta(days=1)
        day_gan_for_hour = _q0_day_pillar(next_day.year, next_day.month, next_day.day)[0]
    else:
        day_gan_for_hour = day_pillar[0]
    hour_pillar = _q0_hour_pillar(day_gan_for_hour, hour)

    bazi_str = f'{year_pillar} {month_pillar} {day_pillar} {hour_pillar}'
    return bazi_str, (year, month, day)

#[v2.0]
def _get_yinyang(day_zhi: str) -> str:
    """日支→阴阳遁: 巳午未申酉戌=阴遁, 亥子丑寅卯辰=阳遁"""
    return '阴' if day_zhi in YIN_ZHI_SET else '阳'

#[v2.0]
def _gong_of_ju(ju: int, yin_yang: str) -> Dict[int, str]:
    """
    根据地盘(局数,阴阳) → 三奇六仪在各宫的分布
    返回: {宫号: 天干}
    阳遁顺排: 戊从ju宫开始, 己庚辛壬癸丁丙乙
    阴遁逆排: 戊从ju宫开始, 乙丙丁癸壬辛庚己
    """
    result = {}
    order = YI_QI_SHUN[:]  # ['戊','己','庚','辛','壬','癸','丁','丙','乙']
    if yin_yang == '阴':
        order = list(reversed(order))  # ['乙','丙','丁','癸','壬','辛','庚','己','戊']

    start_gong = ju
    for i, gan in enumerate(order):
        gong = (start_gong + i - 1) % 9 + 1
        result[gong] = gan
    return result

#[v2.0]
def _get_xun_star(xun_name: str) -> str:
    """旬首 → 值符星名称"""
    idx = XUN_TO_STAR_IDX.get(xun_name, 0)
    # 如果旬首为甲辰/甲寅,对应天禽(4)/天心(5)
    if xun_name == '甲辰':
        return '天禽'
    if xun_name == '甲寅':
        return '天心'
    # 甲子→天蓬(0), 甲戌→天芮(1), 甲申→天冲(2), 甲午→天辅(3)
    name_map = ['天蓬','天芮','天冲','天辅']
    if xun_name in XUN_TO_STAR_IDX:
        idx = XUN_TO_STAR_IDX[xun_name]
        if idx < 4:
            return name_map[idx]
    return '天蓬'

#[v2.0]
def _get_zhishi_men(shizhi: str, yin_yang: str, di_gong_map: Dict[int, str]) -> str:
    """
    值使门: 基于时支定位
    值使门 = 时干所在宫位的原始八门
    简化: 根据时支偏移和阴阳遁确定值使
    """
    if shizhi not in DI_ZHI_IDX:
        return '休'
    zhi_n = DI_ZHI_IDX[shizhi]

    # 八门原始落宫顺序: 休(1),死(2),伤(3),杜(4),开(6),惊(7),生(8),景(9)
    # 根据地支偏移决定值使门
    men_order = ['休','死','伤','杜','开','惊','生','景']
    # 中宫(5)寄坤(2)
    if yin_yang == '阳':
        idx = zhi_n % 8
    else:
        idx = (7 - zhi_n % 8) % 8
    return men_order[idx]

# ── 核心排盘函数 ────────────────────────────────────────────

#[v2.0]
def pai_di_pan(ju: int, yin_yang: str) -> Dict[int, Dict]:
    """
    地盘排盘: 九宫 + 原始三奇六仪
    返回: {宫号: {'gong_name':方位, 'yi_qi':天干, 'wuxing':五行}}
    """
    yi_qi_map = _gong_of_ju(ju, yin_yang)
    di_pan = {}
    for gong in range(1, 10):
        di_pan[gong] = {
            'gong_name': GONG_MAP[gong],
            'gong_num': gong,
            'yi_qi': yi_qi_map.get(gong, ''),
            'wuxing': GONG_WUXING[gong],
        }
    return di_pan

#[v2.0]
def pai_jiu_xing(ju: int, yin_yang: str, time_gan: str, time_zhi: str) -> Dict[int, Dict]:
    """
    九星排盘 (天盘星)
    值符星 = 旬首对应之原始宫位的星
    其他星随值符星飞转
    """
    xun_name = _get_xun(time_gan, time_zhi)
    zhi_fu_star = _get_xun_star(xun_name)

    # 确定值符星原始宫位
    zhi_fu_gong = STAR_GONG.get(zhi_fu_star, 1)

    # 时干所在宫位 = 值符星落宫(天盘)
    yi_qi_map = _gong_of_ju(ju, yin_yang)
    time_gong = 1
    for g, gan in yi_qi_map.items():
        if gan and gan[0] == time_gan:
            time_gong = g
            break

    # 九星飞转: 以值符星落时干宫位为中心, 其他星顺布
    stars_in_order = ['天蓬','天芮','天冲','天辅','天禽','天心','天柱','天任','天英']
    zhi_fu_idx = stars_in_order.index(zhi_fu_star)

    # 重排: 值符星移到第0位 (顺时针旋转)
    rotated = stars_in_order[zhi_fu_idx:] + stars_in_order[:zhi_fu_idx]

    # 按九宫数字顺序布星
    result = {}
    for i, gong in enumerate(range(1, 10)):
        star_name = rotated[i % 9]
        result[gong] = {
            'star': star_name,
            'wuxing': STAR_WUXING.get(star_name, ''),
            'meaning': STAR_MEANING.get(star_name, ''),
            'jixiong': STAR_JIXIONG.get(star_name, '平'),
        }
    return result

#[v2.0]
def pai_ba_shen(yin_yang: str, zhi_fu_gong: int) -> Dict[int, Dict]:
    """
    八神排盘
    阳遁顺排, 阴遁逆排
    值符起于值符宫, 然后腾蛇,太阴,六合,白虎,玄武,九地,九天
    """
    gods = ['值符','腾蛇','太阴','六合','白虎','玄武','九地','九天']
    if yin_yang == '阴':
        # 阴遁逆排
        gods = list(reversed(gods))

    # 从值符宫开始, 顺时针布八神 (八神不入中宫, 中宫寄坤2)
    result = {}
    gong_counter = zhi_fu_gong
    for i, god in enumerate(gods):
        g = (zhi_fu_gong - 1 + i) % 9 + 1
        if g == 5:
            # 中宫寄坤2
            g = 2
        result[g] = {
            'shen': god,
            'meaning': SHEN_MEANING.get(god, ''),
        }
    return result

#[v2.0]
def pai_ba_men(ju: int, yin_yang: str, time_zhi: str, di_pan: Dict[int, Dict]) -> Dict[int, Dict]:
    """
    八门排盘 (人盘)
    值使门 = 基于时支 + 旬首定位
    值使门起于原始宫位, 随时辰飞转
    """
    # 确定值使门
    zhishi = _get_zhishi_men(time_zhi, yin_yang, {})
    zhishi_gong = MEN_GONG.get(zhishi, 1)

    # 八门顺序
    men_order = ['休','死','伤','杜','开','惊','生','景']
    zhishi_idx = men_order.index(zhishi)

    # 阳遁顺转, 阴遁逆转
    result = {}
    for i, gong in enumerate(range(1, 10)):
        if yin_yang == '阳':
            idx = (zhishi_idx + i) % 8
        else:
            idx = (zhishi_idx - i) % 8
        men_name = men_order[idx]
        g = gong
        if g == 5:
            g = 2  # 中宫寄坤
        result[g] = {
            'men': men_name,
            'wuxing': MEN_WUXING.get(men_name, ''),
            'meaning': MEN_MEANING.get(men_name, ''),
            'jixiong': MEN_JIXIONG.get(men_name, '平'),
        }
    return result

#[v2.0]
def pai_tian_pan(ju: int, yin_yang: str, time_gan: str, time_zhi: str,
                 di_pan: Dict[int, Dict]) -> Dict[int, Dict]:
    """
    天盘排盘: 值符星带动奇仪飞转
    天盘奇仪 = 地盘奇仪以值符宫为中点飞转
    """
    xun_name = _get_xun(time_gan, time_zhi)
    zhi_fu_star = _get_xun_star(xun_name)
    zhi_fu_gong = STAR_GONG.get(zhi_fu_star, 1)

    yi_qi_map = _gong_of_ju(ju, yin_yang)
    # 时干宫 = 值符落宫
    time_gong = 1
    for g, gan in yi_qi_map.items():
        if gan and len(gan) > 0 and gan[0] == time_gan:
            time_gong = g
            break

    # 天盘: 值符星落时干宫, 其他星依次飞转
    result = {}
    for gong in range(1, 10):
        # 天盘天干 = 地盘天干随着值符转动
        # 值符星从 zhi_fu_gong → time_gong
        offset = (time_gong - zhi_fu_gong) % 9
        src_gong = (gong - 1 - offset) % 9 + 1
        yi_qi = yi_qi_map.get(src_gong, '')
        result[gong] = {
            'gong_name': GONG_MAP[gong],
            'yi_qi': yi_qi,
            'wuxing': GONG_WUXING[gong],
        }
    return result

#[v2.0]
def pai_ren_pan(ju: int, yin_yang: str, time_zhi: str) -> Dict[int, Dict]:
    """
    人盘排盘: 值使门带动八门飞转
    """
    zhishi = _get_zhishi_men(time_zhi, yin_yang, {})
    zhishi_gong = MEN_GONG.get(zhishi, 1)

    men_order = ['休','死','伤','杜','开','惊','生','景']
    zhishi_idx = men_order.index(zhishi)

    result = {}
    for i, gong in enumerate(range(1, 10)):
        if yin_yang == '阳':
            idx = (zhishi_idx + i) % 8
        else:
            idx = (zhishi_idx - i) % 8
        men_name = men_order[idx]
        g = gong
        if g == 5:
            g = 2
        result[g] = {
            'men': men_name,
            'wuxing': MEN_WUXING.get(men_name, ''),
            'meaning': MEN_MEANING.get(men_name, ''),
            'jixiong': MEN_JIXIONG.get(men_name, '平'),
        }
    return result

# ── 排盘补全 (C2) ───────────────────────────────────────────

KONG_WANG_MAP = {
    '甲子': ('戌','亥'), '甲戌': ('申','酉'), '甲申': ('午','未'),
    '甲午': ('辰','巳'), '甲辰': ('寅','卯'), '甲寅': ('子','丑'),
}

def _calc_kong_wang(xun_name: str) -> list:
    """空亡: 根据旬首计算空亡地支"""
    return list(KONG_WANG_MAP.get(xun_name, []))

MA_ZHI_SETS = [
    (frozenset(['申','子','辰']), '寅'),
    (frozenset(['亥','卯','未']), '巳'),
    (frozenset(['寅','午','戌']), '申'),
    (frozenset(['巳','酉','丑']), '亥'),
]

def _calc_ma_xing(ri_zhi: str, nian_zhi: str = '') -> str:
    """驿马: 日支/年支三合局的对冲位; 日支优先"""
    for zhi_set, ma in MA_ZHI_SETS:
        if ri_zhi in zhi_set:
            return ma
    if nian_zhi:
        for zhi_set, ma in MA_ZHI_SETS:
            if nian_zhi in zhi_set:
                return ma
    return ''

WUXING_KE = {'金':'木', '木':'土', '土':'水', '水':'火', '火':'金'}
GONG_DUI_CHONG = {1:9, 2:8, 3:7, 4:6, 6:4, 7:3, 8:2, 9:1}  # 对冲宫位

def _calc_men_po(men_name: str, gong_num: int) -> str:
    """门迫检测: 门五行克宫五行=门迫, 宫五行克门五行=宫迫"""
    men_wx = MEN_WUXING.get(men_name, '')
    gong_wx = GONG_WUXING.get(gong_num, '')
    if not men_wx or not gong_wx:
        return '无'
    if WUXING_KE.get(men_wx) == gong_wx:
        return '门迫'
    if WUXING_KE.get(gong_wx) == men_wx:
        return '宫迫'
    return '无'

def _calc_yin_gan(ju: int, yin_yang: str, shi_gan: str,
                  di_pan: Dict[int, Dict], tian_pan: Dict[int, Dict]) -> Dict[int, str]:
    """隐干: 王凤麟阴盘 - 时干落值符宫, 其余阳顺阴逆飞布十天干"""
    yi_qi_map = _gong_of_ju(ju, yin_yang)
    # 找时干在原始地盘中的宫位
    zhi_fu_gong = 1
    for g, gan in yi_qi_map.items():
        if gan and len(gan) > 0 and gan[0] == shi_gan:
            zhi_fu_gong = g
            break
    # 隐干 = 每个宫的天盘天干
    yin_gan = {}
    for g in range(1, 10):
        tg = tian_pan.get(g, {}).get('yi_qi', '')
        yin_gan[g] = tg[0] if tg else ''
    return yin_gan

def _calc_fu_yin_fan_yin(jiu_xing: Dict[int, Dict], star_name: str, zhi_fu_gong: int) -> Dict[str, any]:
    """伏吟/反吟检测: 九星伏吟=值符星落原始宫, 反吟=落对冲宫"""
    star_orig_gong = STAR_GONG.get(star_name, 0)
    is_fu_yin = (zhi_fu_gong == star_orig_gong)
    is_fan_yin = (zhi_fu_gong == GONG_DUI_CHONG.get(star_orig_gong, 0))
    return {
        '值符星': star_name,
        '原始宫': star_orig_gong,
        '落宫': zhi_fu_gong,
        '伏吟': is_fu_yin,
        '反吟': is_fan_yin,
    }


# ── 高级分析 ────────────────────────────────────────────────

#[v2.2]
def pai_full(bazi_str: str, date_tuple: Optional[Tuple[int, int, int]] = None) -> Dict[str, Any]:
    """
    完整排盘 #[v2.1] 加入节气定局和中宫处理
    参数:
        bazi_str: 八字四柱
        date_tuple: 可选公历日期 (年,月,日)，用于节气定局
    返回: 包含地盘/天盘/人盘/九星/八神/八门的全量数据
    """
    parsed = _parse_bazi(bazi_str)
    if not parsed:
        return {'error': f'无法解析八字: {bazi_str}'}

    nian_gan, nian_zhi = parsed[0][0], parsed[0][1]
    yue_gan, yue_zhi = parsed[1][0], parsed[1][1]
    ri_gan, ri_zhi = parsed[2][0], parsed[2][1]
    shi_gan, shi_zhi = parsed[3][0], parsed[3][1]

    # 节气定局 (v2.1): 有公历日期时优先使用
    jieqi_used = False
    if date_tuple is not None:
        try:
            j_ju, j_yinyang = _get_ju_from_jieqi(date_tuple[0], date_tuple[1], date_tuple[2])
            yin_yang = j_yinyang
            ju = j_ju
            jieqi_used = True
        except Exception:
            jieqi_used = False

    if not jieqi_used:
        # fallback: v2.0 日干定局
        yin_yang = _get_yinyang(ri_zhi)
        ju = _get_ju_from_gan(ri_gan)

    xun_name = _get_xun(shi_gan, shi_zhi)
    zhi_fu_star = _get_xun_star(xun_name)
    zhi_fu_gong = STAR_GONG.get(zhi_fu_star, 1)

    # 逐盘排布
    di_pan = pai_di_pan(ju, yin_yang)
    jiu_xing = pai_jiu_xing(ju, yin_yang, shi_gan, shi_zhi)
    ba_shen = pai_ba_shen(yin_yang, zhi_fu_gong)
    ba_men = pai_ba_men(ju, yin_yang, shi_zhi, di_pan)
    tian_pan = pai_tian_pan(ju, yin_yang, shi_gan, shi_zhi, di_pan)
    ren_pan = pai_ren_pan(ju, yin_yang, shi_zhi)

    # v2.1: 中宫处理 (天禽坐中,寄坤但保留信息)
    gong_map_raw = {}
    for g in range(1, 10):
        gong_map_raw[g] = {
            'gong_name': GONG_MAP[g],
            'wuxing': GONG_WUXING[g],
            'di_gong': di_pan.get(g, {}),
            'tian_gong': tian_pan.get(g, {}),
            'jiu_xing': jiu_xing.get(g, {}),
            'ba_men': ren_pan.get(g, {}),
            'ba_shen': ba_shen.get(g, {}),
        }

    gong_map_processed = _handle_zhong_gong(gong_map_raw)

    # 综合每个宫的完整信息 (v2.1: 包含中宫)
    gong_details = {}
    for g in range(1, 10):
        gong_info = gong_map_processed.get(g, {})
        # 跳过中宫(5)不显示在宫位详情中 (主要信息通过寄宫传递)
        if g == 5:
            continue

        detail = {
            '方位': GONG_MAP[g],
            '五行': GONG_WUXING[g],
            '地盘': (gong_info.get('di_gong', {}) or {}).get('yi_qi', ''),
            '天盘': (gong_info.get('tian_gong', {}) or {}).get('yi_qi', ''),
            '九星': (gong_info.get('jiu_xing', {}) or {}).get('star', ''),
            '星吉凶': (gong_info.get('jiu_xing', {}) or {}).get('jixiong', ''),
            '八门': (gong_info.get('ba_men', {}) or {}).get('men', ''),
            '门吉凶': (gong_info.get('ba_men', {}) or {}).get('jixiong', ''),
            '门意义': (gong_info.get('ba_men', {}) or {}).get('meaning', ''),
            '八神': (gong_info.get('ba_shen', {}) or {}).get('shen', ''),
            '神意义': (gong_info.get('ba_shen', {}) or {}).get('meaning', ''),
        }

        # v2.1: 传递中宫寄宫信息
        if gong_info.get('zhong_gong'):
            detail['中宫寄'] = True
            detail['中宫信息'] = gong_info.get('zhong_gong_note', '')

        gong_details[g] = detail

    # ── 排盘补全 (C2) ──
    kong_wang = _calc_kong_wang(xun_name)
    ma_xing = _calc_ma_xing(ri_zhi)
    fu_yin_info = _calc_fu_yin_fan_yin(jiu_xing, zhi_fu_star, zhi_fu_gong)
    yin_gan = _calc_yin_gan(ju, yin_yang, shi_gan, di_pan, tian_pan)
    # 门迫: 追加到宫位详情
    for g in range(1, 10):
        if g == 5:
            continue
        if g in gong_details:
            men_name = gong_details[g].get('八门', '')
            gong_details[g]['门迫'] = _calc_men_po(men_name, g)
    # 隐干: 追加到宫位详情
    for g in range(1, 10):
        if g == 5:
            continue
        if g in gong_details:
            gong_details[g]['隐干'] = yin_gan.get(g, '')

    result = {
        '方法': '奇门遁甲v2.2',
        '局': f'{yin_yang}{ju}局',
        '阴阳': yin_yang,
        '局数': ju,
        '年柱': parsed[0],
        '月柱': parsed[1],
        '日柱': parsed[2],
        '时柱': parsed[3],
        '旬首': xun_name,
        '值符星': zhi_fu_star,
        '值符宫': zhi_fu_gong,
        '空亡': kong_wang,
        '驿马': ma_xing,
        '伏吟反吟': fu_yin_info,
        '地盘': di_pan,
        '天盘': tian_pan,
        '人盘(八门)': ren_pan,
        '九星': jiu_xing,
        '八神': ba_shen,
        '宫位详情': gong_details,
        '中宫处理': gong_map_processed.get(5, {}),
    }

    # v2.1: 标记定局方式
    if jieqi_used:
        result['定局方式'] = '节气定局'
        result['节气信息'] = date_tuple
    else:
        result['定局方式'] = '日干定局(备选)'

    return result

#[v2.0]
def calc_qimen_wealth(analyze_result: dict) -> int:
    """
    财富信号评分 [-4, +4]  #[v2.1] 加入用神体系
    规则:
    - 生门在财帛宫位(艮8/巽4/离9) +3
    - 开门 +2
    - 休门 +1
    - 三奇(乙丙丁)落生门 +2
    - 凶门(死惊伤)在财位 -2
    - [v2.1] 用神落宫吉凶: 生门+戊在财宫=最大吉 +2
    - [v2.1] 三奇乙丙丁落吉门 +1
    """
    try:
        score = 0
        ba_men = analyze_result.get('人盘(八门)', {})
        gong_details = analyze_result.get('宫位详情', {})

        # ── v2.2: 用神检查 + 凶门用神罚 ─────────────────────
        yong_shen = analyze_result.get('用神', {})
        if yong_shen:
            ys_men = yong_shen.get('yong_shen_men', '')
            ys_gan = yong_shen.get('yong_shen_gan', '')
            ys_gong = yong_shen.get('yong_shen_gong', 0)

            for gong_num, info in gong_details.items():
                men = info.get('八门', '')
                tian_gan = info.get('天盘', '')
                di_gan = info.get('地盘', '')
                is_caiwei = gong_num in (8, 4, 9)

                # 用神之门(生)在财宫 +2 (v2.1)
                if men == ys_men and is_caiwei:
                    score += 2
                # 用神之干(戊)在吉门宫 +1
                if (tian_gan == ys_gan or di_gan == ys_gan) and men in ('生', '开', '休'):
                    score += 1
                # 三奇乙丙丁落吉门 +1 (v2.1补充)
                san_qi = {'乙', '丙', '丁'}
                has_san_qi = (tian_gan in san_qi) or (di_gan in san_qi)
                if has_san_qi and men in ('生', '开', '休'):
                    score += 1
                # [v2.2] 用神落凶门罚 → -1
                if men in ('死', '惊', '伤') and (tian_gan == ys_gan or di_gan == ys_gan):
                    score -= 1

        # ── v2.0 原有评分逻辑 ────────────────────────────────
        # 注意: 仅在无用神时执行完整v2.0评分; 有用神时只补充
        # 开门/休门/凶门条件(避免与用神检查对生门+财位重复计分)
        for gong_num, info in gong_details.items():
            men = info.get('八门', '')
            is_caiwei = gong_num in (8, 4, 9)

            # 生门在财帛宫位(有用神时已由用神检查计分,此处跳过)
            if men == '生' and is_caiwei and not yong_shen:
                score += 3
            # 开门
            elif men == '开':
                score += 2
            # 休门
            elif men == '休':
                score += 1
            # 凶门在财位
            elif men in ('死','惊','伤') and is_caiwei:
                score -= 2

        # [v2.1] 备选: 如果gong_details评分=0，从ren_pan直接读
        if score == 0:
            ba_men_raw = analyze_result.get('人盘(八门)', {})
            men_seen = set()
            for gong_num, men_info in ba_men_raw.items():
                if isinstance(men_info, dict):
                    men_name = men_info.get('men', '')
                    men_seen.add(men_name)
                    if men_name == '生':
                        score = max(score, 3)
                    elif men_name == '开':
                        score = max(score, 2)
                    elif men_name == '休':
                        score = max(score, 1)
            if not men_seen.intersection({'生', '开', '休'}):
                for gong_num, men_info in ba_men_raw.items():
                    if isinstance(men_info, dict):
                        men_name = men_info.get('men', '')
                        if men_name in ('死', '惊', '伤'):
                            score = min(score, -1)
                            break

        # 三奇(乙丙丁)落生门: 有用神时已由用神三奇条件覆盖,此处仅备选
        if not yong_shen:
            for gong_num, info in gong_details.items():
                tian_pan_gan = info.get('天盘', '')
                di_pan_gan = info.get('地盘', '')
                men = info.get('八门', '')
                san_qi = {'乙','丙','丁'}
                has_san_qi = (tian_pan_gan in san_qi) or (di_pan_gan in san_qi)
                if men == '生' and has_san_qi:
                    score += 2

        # 限制范围 [-4, +4]
        score = max(-4, min(4, score))
        return score

    except Exception:
        return 0

#[v2.0]
def analyze_lifetime(nian_gan: str, nian_zhi: str) -> Dict[str, Any]:
    """
    终身局分析: 用年柱定局, 不依赖具体时间
    分析一生财富格局
    """
    # 年柱定阴阳 (沿用日支规则,但终身局用年支)
    yin_yang = '阴' if nian_zhi in YIN_ZHI_SET else '阳'
    ju = _get_ju_from_gan(nian_gan)

    # 用午时作为默认时辰 (代表一生)
    shi_gan, shi_zhi = '丙', '午'

    # 构建虚拟八字
    virtual_bazi = f'{nian_gan}{nian_zhi} 甲子 {nian_gan}{nian_zhi} {shi_gan}{shi_zhi}'
    full = pai_full(virtual_bazi)
    full['终身局'] = True
    full['年干'] = nian_gan
    full['年支'] = nian_zhi

    # 财富评分
    wealth_score = calc_qimen_wealth(full)

    # 财富解读
    wealth_levels = {
        -4: '⚠️ 财富风险极高,宜守不宜攻',
        -3: '⚠️ 财运不畅,谨慎投资',
        -2: '🔻 财来财去,需防破财',
        -1: '➖ 财运平缓,小有损耗',
        0: '➖ 财运平稳,无大起大落',
        1: '🟢 财运尚可,有进有出',
        2: '🟢 财运不错,可望增长',
        3: '💰 财运亨通,生财有道',
        4: '💰💰 大富之象,财源广进',
    }

    full['财富评分'] = wealth_score
    full['财富解读'] = wealth_levels.get(wealth_score, '财运平稳')
    full['分析类型'] = '终身局'

    return full

#[v2.1 / Q0]
def analyze(bazi_str: str = '丙寅 戊戌 辛丑 壬辰', gender: str = '男',
            question_type: str = 'wealth',
            date_tuple: Optional[Tuple[int, int, int]] = None,
            chart_mode: str = 'birth') -> Dict[str, Any]:
    """
    奇门遁甲分析主入口  #[v2.1 / Q0]
    参数:
        bazi_str: 八字四柱, e.g. '丙寅 戊戌 辛丑 壬辰'
        gender: 性别 ('男'/'女')
        question_type: 问题类型 ('wealth'/'general'/'love'/'career'/'health')
        date_tuple: 可选公历日期 (年,月,日)，用于节气定局
        chart_mode: 'birth'=生辰/演示盘（标非问事时盘）；'question'=真问事时盘
    返回:
        包含完整排盘、用神、评分和解读的字典
    真问事请用 analyze_question(datetime)；无 datetime 须拒答。
    """
    try:
        parsed = _parse_bazi(bazi_str)
        if not parsed:
            return {
                'method': '奇门遁甲v2.0',
                'error': f'八字格式错误: {bazi_str}',
                '局': '未知',
            }

        # 完整排盘 (v2.1: 传入date_tuple启用节气定局)
        full = pai_full(bazi_str, date_tuple=date_tuple)
        if 'error' in full:
            full['method'] = '奇门遁甲v2.0'
            return full

        # v2.1: 用神体系
        yong_shen = _get_yong_shen(parsed, question_type)
        gong_details = full.get('宫位详情', {})

        # Q0: 用神落宫 = 符号实落（门优先），禁固定读 reference_gong
        loc = locate_yong_shen_gong(
            gong_details,
            men=yong_shen.get('yong_shen_men'),
            gan=yong_shen.get('yong_shen_gan'),
        )
        ys_gong = loc.get('gong')
        if ys_gong is not None:
            yong_shen['yong_shen_gong'] = ys_gong
            yong_shen['yong_shen_locate_by'] = loc.get('by')
        full['用神'] = yong_shen
        full['用神描述'] = yong_shen.get('yong_shen_description', '')

        if ys_gong and ys_gong in gong_details:
            ys_info = gong_details[ys_gong]
            full['用神落宫'] = {
                '宫': ys_gong,
                '方位': GONG_MAP.get(ys_gong, ''),
                '八门': ys_info.get('八门', ''),
                '门吉凶': ys_info.get('门吉凶', ''),
                '九星': ys_info.get('九星', ''),
                '天盘': ys_info.get('天盘', ''),
                '地盘': ys_info.get('地盘', ''),
                '定位方式': loc.get('by'),
                '参考宫': yong_shen.get('yong_shen_reference_gong'),
                '门实落宫': loc.get('men_gong'),
                '干天盘宫': loc.get('gan_gong_tian'),
                '干地盘宫': loc.get('gan_gong_di'),
            }
        else:
            full['用神落宫'] = {
                '宫': None,
                '定位方式': None,
                '参考宫': yong_shen.get('yong_shen_reference_gong'),
                'note': '符号未在盘面定位',
            }

        # Q0 盘类型标注
        if chart_mode == 'question':
            full['盘类型'] = QUESTION_CHART_LABEL
            full['非问事时盘'] = False
        else:
            full['盘类型'] = NON_QUESTION_CHART_LABEL
            full['非问事时盘'] = True
            full['disclaimer'] = (
                '非问事时盘：按生辰/演示起局，仅作符号对照；'
                '真问事须提供 datetime 并调用 analyze_question。'
            )

        # 财富评分
        if question_type == 'wealth':
            wealth_score = calc_qimen_wealth(full)
            full['财富评分'] = wealth_score

            # 详细的财富解读 (v2.1: 加入用神信息)
            ys_desc = yong_shen.get('yong_shen_description', '')
            if wealth_score >= 3:
                full['财富解读'] = f'💰 财运亨通!生门临财宫,财源广进之象。{ys_desc}'
            elif wealth_score >= 1:
                full['财富解读'] = f'🟢 财运不错,有财可求。{ys_desc}'
            elif wealth_score <= -2:
                full['财富解读'] = f'⚠️ 财运不佳,谨慎守成为上。{ys_desc}'
            else:
                full['财富解读'] = f'➖ 财运平稳,按部就班。{ys_desc}'

        # 最佳方向
        good_doors = []
        for g, info in full.get('宫位详情', {}).items():
            men = info.get('八门', '')
            if men in ('开', '休', '生'):
                good_doors.append(f"{info.get('方位','')}({men}门)")

        full['最佳方向'] = '、'.join(good_doors[:3]) if good_doors else '西北(开门)'

        # 解读文本
        ju_str = full.get('局', '')
        ri_zhu = full.get('日柱', '')
        men_info = full.get('人盘(八门)', {})

        good_men_list = []
        for g, info in men_info.items():
            if info.get('jixiong') == '大吉':
                good_men_list.append(info.get('men', ''))

        zhi_fu = full.get('值符星', '')
        wealth_txt = full.get('财富解读', '')

        full['解读'] = (
            f"{ju_str} {ri_zhu}日主。"
            f"值符{zhi_fu}。"
            f"吉门:{','.join(good_men_list) if good_men_list else '无'}。"
            f"{wealth_txt}"
        )

        full['method'] = '奇门遁甲v2.0'
        full['性别'] = gender
        full['问题类型'] = question_type

        return full

    except Exception as e:
        return {
            'method': '奇门遁甲v2.0',
            'error': str(e),
            '局': '排盘出错',
        }


def analyze_question(
    question_dt=None,
    *,
    question_type: str = 'wealth',
    gender: str = '男',
) -> Dict[str, Any]:
    """
    Q0 真问事时盘合同入口。
    - 必须提供问事 datetime；否则拒答（refused=True）。
    - datetime → 日时柱 + 节气定局；用神落宫=符号实落。
    - 不做 B6 叙事附录（仅结构盘）。
    """
    if question_dt is None:
        return {
            'method': '奇门遁甲v2.0',
            'refused': True,
            'refuse_reason': REFUSE_NO_DATETIME,
            '盘类型': None,
            '非问事时盘': None,
            '局': None,
        }
    try:
        from datetime import datetime as dt_cls
        if not isinstance(question_dt, dt_cls):
            return {
                'method': '奇门遁甲v2.0',
                'refused': True,
                'refuse_reason': REFUSE_NO_DATETIME + '（须为 datetime 实例）',
                '盘类型': None,
                '局': None,
            }
        bazi_str, date_tuple = datetime_to_question_pillars(question_dt)
        full = analyze(
            bazi_str,
            gender=gender,
            question_type=question_type,
            date_tuple=date_tuple,
            chart_mode='question',
        )
        full['refused'] = False
        full['问事时间'] = question_dt.isoformat(sep=' ', timespec='minutes')
        full['问事四柱'] = bazi_str
        return full
    except Exception as e:
        return {
            'method': '奇门遁甲v2.0',
            'refused': True,
            'refuse_reason': f'问事起局失败: {e}',
            '盘类型': None,
            '局': None,
        }

#[v2.0]
def format_report(r: dict) -> str:
    """格式化输出为HTML"""
    try:
        h = '<div style="font-size:12px;font-family:sans-serif;">'

        # Q0: 无 datetime 拒答
        if r.get('refused'):
            reason = r.get('refuse_reason', REFUSE_NO_DATETIME)
            h += (
                f'<div style="margin:6px 0;padding:8px;border-left:4px solid #c62828;'
                f'background:#ffebee;border-radius:4px;">'
                f'<b>⛔ 拒答</b>：{reason}</div></div>'
            )
            return h

        # 标题
        method = r.get('method', '奇门遁甲')
        ju = r.get('局', '-')
        h += f'<p><b>🔮 {method}</b> 局: {ju}'

        if '日柱' in r:
            h += f' 日柱: {r["日柱"]}'
        if '年柱' in r:
            h += f' 年柱: {r["年柱"]}'
        h += '</p>'

        # Q0: 盘类型标注（生辰=非问事时盘）
        chart_label = r.get('盘类型')
        if chart_label:
            color = '#c62828' if r.get('非问事时盘') else '#2e7d32'
            h += (
                f'<p style="margin:4px 0;padding:4px 6px;border-left:3px solid {color};'
                f'background:#fafafa;font-size:11px;"><b>盘类型</b>：{chart_label}'
            )
            if r.get('disclaimer'):
                h += f'<br>{r["disclaimer"]}'
            h += '</p>'

        # 基本信息
        if '值符星' in r:
            h += f'<p>值符: {r["值符星"]}'
            if '旬首' in r:
                h += f' 旬首: {r["旬首"]}'
            if '定局方式' in r:
                h += f' 定局: {r["定局方式"]}'
            h += '</p>'

        # v2.1: 用神信息
        if '用神描述' in r:
            ys_desc = r['用神描述']
            ys_luogong = r.get('用神落宫', {})
            if ys_luogong:
                ys_fangwei = ys_luogong.get('方位', '')
                ys_men = ys_luogong.get('八门', '')
                ys_men_jx = ys_luogong.get('门吉凶', '')
                h += f'<p style="margin:4px 0;padding:4px;background:#fff3e0;border-radius:4px;">'
                h += f'<b>🔮 用神:</b> {ys_desc}'
                h += f'<br>落宫: {ys_fangwei}{ys_luogong.get("宫","")} | 门: {ys_men}({ys_men_jx})'
                if '九星' in ys_luogong:
                    h += f' | 星: {ys_luogong["九星"]}'
                h += '</p>'
            else:
                h += f'<p style="margin:2px 0;color:#666;"><b>🔮 用神:</b> {ys_desc}</p>'

        # v2.1: 中宫信息
        if '中宫处理' in r and r.get('中宫处理'):
            zhong = r['中宫处理']
            zhong_note = zhong.get('zhong_gong_note', '天禽坐中寄坤')
            h += f'<p style="margin:2px 0;color:#888;font-size:11px;">🏮 中宫: {zhong_note}</p>'

        # 宫位详情 (简表)
        details = r.get('宫位详情', {})
        if details:
            h += '<table style="border-collapse:collapse;width:100%;margin:4px 0;">'
            h += '<tr style="background:#f5f5f5;"><th>宫</th><th>方位</th><th>九星</th><th>八门</th><th>八神</th><th>天盘</th><th>地盘</th></tr>'
            for g in sorted(details.keys()):
                info = details[g]
                men = info.get('八门', '')
                men_jx = info.get('门吉凶', '')
                men_bg = '#e8f5e9' if men_jx == '大吉' else '#fffde7' if men_jx in ('平','小吉') else '#ffebee' if '凶' in men_jx else '#fff'

                h += f'<tr style="border:1px solid #ddd;">'
                h += f'<td style="padding:2px 4px;">{info.get("方位","")}{g}</td>'
                h += f'<td style="padding:2px 4px;">{GONG_MAP.get(g,"")}</td>'
                h += f'<td style="padding:2px 4px;">{info.get("九星","")}</td>'
                h += f'<td style="padding:2px 4px;background:{men_bg};">{men}({men_jx})</td>'
                h += f'<td style="padding:2px 4px;">{info.get("八神","")}</td>'
                h += f'<td style="padding:2px 4px;">{info.get("天盘","")}</td>'
                h += f'<td style="padding:2px 4px;">{info.get("地盘","")}</td>'
                h += '</tr>'
            h += '</table>'

        # 财富评分
        if '财富评分' in r:
            ws = r['财富评分']
            wt = r.get('财富解读', '')
            ws_color = '#4caf50' if ws >= 2 else '#ff9800' if ws >= 0 else '#f44336'
            h += f'<p style="margin:4px 0;">财富评分: <span style="font-size:16px;font-weight:bold;color:{ws_color};">{ws:+d}</span> {wt}</p>'

        # 最佳方向
        if '最佳方向' in r:
            h += f'<p>🧭 最佳方向: {r["最佳方向"]}</p>'

        # 解读
        if '解读' in r:
            h += f'<p style="margin-top:4px;padding:6px;background:#f3e5f5;border-radius:4px;">{r["解读"]}</p>'

        h += '</div>'
        return h

    except Exception:
        return '<div>⚠️ 格式输出错误</div>'


#[v2.3]
def get_liu_nian_qimen(bazi_str: str, gender: str = '男',
                       target_year: int = 2026,
                       question_type: str = 'general') -> Dict[str, Any]:
    """
    流年奇门分析 #[v2.3]
    计算出生八字奇门盘, 结合流年天干落宫评估年度吉凶

    参数:
        bazi_str: 八字四柱
        gender: 性别
        target_year: 目标年份 (如2026)
        question_type: 用神类型 (wealth/career/health/general)

    返回:
        {
            year: 目标年份,
            liu_nian_gan: 流年天干,
            luo_gong: 流年天干落宫编号,
            palace_strength: 宫位力量(-1~1),
            wealth_impact: 财运影响,
            career_impact: 事业影响,
            health_impact: 健康影响,
        }
    """
    # 1. 排盘
    qimen_result = analyze(bazi_str, gender=gender, question_type=question_type)
    if 'error' in qimen_result:
        return {'error': qimen_result['error']}

    # 2. 流年天干地支
    gan = TIAN_GAN[(target_year - 4) % 10]
    zhi = DI_ZHI[(target_year - 4) % 12]

    # 3. 流年天干落宫 (按天干五行纳宫)
    LIU_NIAN_LUO_GONG = {
        '甲': 1, '乙': 2, '丙': 3, '丁': 4, '戊': 5,
        '己': 6, '庚': 7, '辛': 8, '壬': 9, '癸': 1,
    }
    luo_gong = LIU_NIAN_LUO_GONG.get(gan, 1)

    # 4. 用神落宫
    yong_shen = qimen_result.get('用神落宫', {}) or {}
    yong_shen_gong = yong_shen.get('宫', 1)

    # 5. 五行生克关系
    liu_wx = GONG_WUXING.get(luo_gong, '土')
    yong_wx = GONG_WUXING.get(yong_shen_gong, '土')

    WUXING_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}

    if WUXING_SHENG.get(liu_wx) == yong_wx:
        palace_strength = 1.0    # 流年生用神 → 吉
    elif WUXING_SHENG.get(yong_wx) == liu_wx:
        palace_strength = 0.0    # 用神生流年 → 平
    elif WUXING_KE.get(liu_wx) == yong_wx:
        palace_strength = -1.0   # 流年克用神 → 凶
    elif WUXING_KE.get(yong_wx) == liu_wx:
        palace_strength = -0.5   # 用神克流年 → 微凶
    else:
        palace_strength = 0.5    # 比和 → 小吉

    # 6. 分项影响 (根据用神类型分配)
    impact = 1 if palace_strength > 0.5 else (-1 if palace_strength < -0.5 else 0)
    weak_impact = 1 if palace_strength > 0 else (-1 if palace_strength < 0 else 0)
    flat = 0

    impact_map = {
        'wealth': (impact, flat, flat),
        'career': (flat, impact, flat),
        'health': (flat, flat, impact),
        'general': (weak_impact, weak_impact, weak_impact),
        'love': (flat, weak_impact, flat),
    }
    if question_type not in impact_map:
        question_type = 'general'
    w_imp, c_imp, h_imp = impact_map[question_type]

    return {
        'year': target_year,
        'liu_nian_gan': gan,
        'liu_nian_zhi': zhi,
        'luo_gong': luo_gong,
        'luo_gong_name': GONG_MAP.get(luo_gong, ''),
        'palace_strength': palace_strength,
        'yong_shen_gong': yong_shen_gong,
        'yong_shen_men': yong_shen.get('八门', ''),
        'yong_shen_star': yong_shen.get('九星', ''),
        'wealth_impact': w_imp,
        'career_impact': c_imp,
        'health_impact': h_imp,
    }


# ── 快速测试 ────────────────────────────────────────────────

if __name__ == '__main__':
    test_bazi = '丙寅 戊戌 辛丑 壬辰'

    print('=' * 50)
    print('🔮 奇门遁甲 v2.1 测试')
    print('=' * 50)

    # 测试1: 传统日干定局 (v2.0兼容)
    print('\n【测试1】日干定局 + 用神(wealth)')
    result1 = analyze(test_bazi, gender='男', question_type='wealth')
    print(f'八字: {test_bazi}')
    print(f'局: {result1.get("局","")}')
    print(f'定局方式: {result1.get("定局方式","")}')
    print(f'值符星: {result1.get("值符星","")}')
    print(f'旬首: {result1.get("旬首","")}')
    print(f'用神: {result1.get("用神描述","")}')
    ys_luogong = result1.get('用神落宫', {})
    if ys_luogong:
        print(f'用神落宫: {ys_luogong.get("方位","")}{ys_luogong.get("宫","")} '
              f'门:{ys_luogong.get("八门","")}({ys_luogong.get("门吉凶","")})')
    print(f'财富评分: {result1.get("财富评分",0):+d}')
    print(f'财富解读: {result1.get("财富解读","")}')
    print(f'最佳方向: {result1.get("最佳方向","")}')

    # 测试2: 节气定局 (v2.1新功能)
    print('\n【测试2】节气定局 (2024年3月21日春分)')
    result2 = analyze(test_bazi, gender='男', question_type='wealth',
                      date_tuple=(2024, 3, 21))
    print(f'八字: {test_bazi}')
    print(f'局: {result2.get("局","")}')
    print(f'定局方式: {result2.get("定局方式","")}')
    print(f'用神: {result2.get("用神描述","")}')
    print(f'财富评分: {result2.get("财富评分",0):+d}')

    # 测试3: 事业用神
    print('\n【测试3】节气定局 + 事业用神 (2024年6月15日)')
    result3 = analyze(test_bazi, gender='男', question_type='career',
                      date_tuple=(2024, 6, 15))
    print(f'局: {result3.get("局","")}')
    print(f'定局方式: {result3.get("定局方式","")}')
    print(f'用神: {result3.get("用神描述","")}')
    ys_luogong3 = result3.get('用神落宫', {})
    if ys_luogong3:
        print(f'用神落宫: {ys_luogong3.get("方位","")}{ys_luogong3.get("宫","")} '
              f'门:{ys_luogong3.get("八门","")}({ys_luogong3.get("门吉凶","")})')

    # 测试4: 健康用神
    print('\n【测试4】健康用神 (health)')
    result4 = analyze(test_bazi, gender='男', question_type='health',
                      date_tuple=(2024, 12, 25))
    print(f'局: {result4.get("局","")}')
    print(f'定局方式: {result4.get("定局方式","")}')
    print(f'用神: {result4.get("用神描述","")}')

    print()
    print('=' * 50)
    print('📋 HTML报告 (测试1)')
    print('=' * 50)
    print(format_report(result1))
