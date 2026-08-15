"""
12 Zodiac signs data + date range lookup.
"""
from typing import Optional

ZODIAC = [
    {"sign": "aries",       "name_en": "Aries",       "name_cn": "白羊座", "symbol": "♈", "dates": "03.21-04.19", "element": "fire",  "ruler": "Mars",    "keywords": "勇气 行动 开拓 热情 冲动"},
    {"sign": "taurus",      "name_en": "Taurus",      "name_cn": "金牛座", "symbol": "♉", "dates": "04.20-05.20", "element": "earth", "ruler": "Venus",   "keywords": "稳定 务实 感官 耐心 固执"},
    {"sign": "gemini",      "name_en": "Gemini",      "name_cn": "双子座", "symbol": "♊", "dates": "05.21-06.21", "element": "air",   "ruler": "Mercury", "keywords": "灵活 沟通 好奇 多变 焦躁"},
    {"sign": "cancer",      "name_en": "Cancer",      "name_cn": "巨蟹座", "symbol": "♋", "dates": "06.22-07.22", "element": "water", "ruler": "Moon",    "keywords": "情感 敏感 守护 怀旧 依赖"},
    {"sign": "leo",         "name_en": "Leo",         "name_cn": "狮子座", "symbol": "♌", "dates": "07.23-08.22", "element": "fire",  "ruler": "Sun",     "keywords": "自信 慷慨 领导 骄傲 虚荣"},
    {"sign": "virgo",       "name_en": "Virgo",       "name_cn": "处女座", "symbol": "♍", "dates": "08.23-09.22", "element": "earth", "ruler": "Mercury", "keywords": "分析 完美 服务 挑剔 焦虑"},
    {"sign": "libra",       "name_en": "Libra",       "name_cn": "天秤座", "symbol": "♎", "dates": "09.23-10.23", "element": "air",   "ruler": "Venus",   "keywords": "平衡 和谐 审美 犹豫 讨好"},
    {"sign": "scorpio",     "name_en": "Scorpio",     "name_cn": "天蝎座", "symbol": "♏", "dates": "10.24-11.22", "element": "water", "ruler": "Pluto",   "keywords": "深刻 执着 洞察 掌控 嫉妒"},
    {"sign": "sagittarius", "name_en": "Sagittarius", "name_cn": "射手座", "symbol": "♐", "dates": "11.23-12.21", "element": "fire",  "ruler": "Jupiter", "keywords": "自由 乐观 探索 直率 鲁莽"},
    {"sign": "capricorn",   "name_en": "Capricorn",   "name_cn": "摩羯座", "symbol": "♑", "dates": "12.22-01.19", "element": "earth", "ruler": "Saturn",  "keywords": "雄心 纪律 责任 保守 冷漠"},
    {"sign": "aquarius",    "name_en": "Aquarius",    "name_cn": "水瓶座", "symbol": "♒", "dates": "01.20-02.18", "element": "air",   "ruler": "Uranus",  "keywords": "独立 创新 理想 疏离 叛逆"},
    {"sign": "pisces",      "name_en": "Pisces",      "name_cn": "双鱼座", "symbol": "♓", "dates": "02.19-03.20", "element": "water", "ruler": "Neptune", "keywords": "梦幻 共情 直觉 逃避 敏感"},
]

ZODIAC_BY_NAME = {z["sign"]: z for z in ZODIAC}
ZODIAC_BY_CN = {z["name_cn"]: z for z in ZODIAC}
# 额外索引：按 name_en 大写形式查（兼容 "Scorpio"/"SCORPIO" 等大小写输入）
ZODIAC_BY_EN = {z["name_en"].upper(): z for z in ZODIAC}


def normalize_sign(raw: str) -> Optional[str]:
    """
    把用户输入的星座标识规范化为 ZODIAC_BY_NAME 的 key（小写英文 sign）。
    接受：小写 sign（"scorpio"）、大写 name_en（"Scorpio"/"SCORPIO"）、
    中文 name_cn（"天蝎座"）；自动 strip 首尾空白。无法识别时返回 None。
    """
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    if s in ZODIAC_BY_NAME:           # "scorpio"
        return s
    if s in ZODIAC_BY_CN:             # "天蝎座"
        return ZODIAC_BY_CN[s]["sign"]
    up = s.upper()
    if up in ZODIAC_BY_EN:            # "Scorpio" / "SCORPIO"
        return ZODIAC_BY_EN[up]["sign"]
    low = s.lower()
    if low in ZODIAC_BY_NAME:         # 容错：大小写不一的小写输入
        return low
    return None

_BOUNDARIES = [
    (1, 20, "aquarius"), (2, 19, "pisces"), (3, 21, "aries"), (4, 20, "taurus"),
    (5, 21, "gemini"), (6, 22, "cancer"), (7, 23, "leo"), (8, 23, "virgo"),
    (9, 23, "libra"), (10, 24, "scorpio"), (11, 23, "sagittarius"), (12, 22, "capricorn"),
]


def get_sign_by_date(month: int, day: int):
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    for i, (m, d_start, sign) in enumerate(_BOUNDARIES):
        if m == month:
            if day >= d_start:
                return sign
            prev = _BOUNDARIES[i - 1] if i > 0 else _BOUNDARIES[-1]
            return prev[2]
    return None
