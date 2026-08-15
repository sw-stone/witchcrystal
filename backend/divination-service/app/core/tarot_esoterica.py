"""
Esoteric associations for the 78-card Rider-Waite tarot deck.

Provides element, astrology, chakra, crystal, numerology, and color correspondences
for each card. These enrich the LLM prompt with deeper symbolic context.

This is a separate lookup keyed by card ID, kept apart from tarot_data.py
to avoid inflating the main deck definition. Use CARD_ESOTERICA[id] to access.
"""

CARD_ESOTERICA = {
    # ── Major Arcana ──────────────────────────────────────────────
    0: {"element": "风", "astrology": "天王星", "chakra": "顶轮", "crystal": "白水晶", "numerology": "0(无限)", "color": "明黄"},
    1: {"element": "风", "astrology": "水星", "chakra": "喉轮", "crystal": "黄水晶", "numerology": "1", "color": "黄"},
    2: {"element": "水", "astrology": "月亮", "chakra": "第三眼", "crystal": "月光石", "numerology": "2", "color": "银白"},
    3: {"element": "土", "astrology": "金星", "chakra": "心轮", "crystal": "祖母绿", "numerology": "3", "color": "翠绿"},
    4: {"element": "火", "astrology": "白羊", "chakra": "太阳神经丛", "crystal": "红碧玉", "numerology": "4", "color": "朱红"},
    5: {"element": "土", "astrology": "金牛", "chakra": "喉轮", "crystal": "青金石", "numerology": "5", "color": "深蓝"},
    6: {"element": "风", "astrology": "双子", "chakra": "心轮", "crystal": "粉晶", "numerology": "6", "color": "粉红"},
    7: {"element": "水", "astrology": "巨蟹", "chakra": "太阳神经丛", "crystal": "红玛瑙", "numerology": "7", "color": "深蓝"},
    8: {"element": "火", "astrology": "狮子", "chakra": "心轮", "crystal": "太阳石", "numerology": "8(无限)", "color": "橙黄"},
    9: {"element": "土", "astrology": "处女", "chakra": "顶轮", "crystal": "烟晶", "numerology": "9", "color": "灰褐"},
    10: {"element": "火", "astrology": "木星", "chakra": "心轮", "crystal": "橄榄石", "numerology": "10", "color": "翠绿"},
    11: {"element": "风", "astrology": "天秤", "chakra": "心轮", "crystal": "蓝玉髓", "numerology": "11", "color": "天蓝"},
    12: {"element": "水", "astrology": "海王", "chakra": "顶轮", "crystal": "紫水晶", "numerology": "12", "color": "靛蓝"},
    13: {"element": "火", "astrology": "天蝎", "chakra": "海底轮", "crystal": "黑曜石", "numerology": "13", "color": "黑"},
    14: {"element": "火", "astrology": "射手", "chakra": "心轮", "crystal": "蓝砂石", "numerology": "14", "color": "天蓝"},
    15: {"element": "土", "astrology": "摩羯", "chakra": "海底轮", "crystal": "黑碧玺", "numerology": "15", "color": "黑红"},
    16: {"element": "火", "astrology": "火星", "chakra": "海底轮", "crystal": "红发晶", "numerology": "16", "color": "赤红"},
    17: {"element": "风", "astrology": "水瓶", "chakra": "顶轮", "crystal": "海蓝宝", "numerology": "17", "color": "湖蓝"},
    18: {"element": "水", "astrology": "双鱼", "chakra": "第三眼", "crystal": "月光石", "numerology": "18", "color": "银灰"},
    19: {"element": "火", "astrology": "太阳", "chakra": "太阳神经丛", "crystal": "黄水晶", "numerology": "19", "color": "金黄"},
    20: {"element": "火", "astrology": "冥王", "chakra": "心轮", "crystal": "红宝石", "numerology": "20", "color": "红金"},
    21: {"element": "土", "astrology": "土星", "chakra": "顶轮", "crystal": "紫水晶", "numerology": "21", "color": "紫"},

    # ── Wands (Fire) ──────────────────────────────────────────────
    22: {"element": "火", "astrology": "白羊/狮子/射手", "chakra": "太阳神经丛", "crystal": "红玛瑙", "numerology": "Ace", "color": "红"},
    23: {"element": "火", "astrology": "白羊", "chakra": "太阳神经丛", "crystal": "红碧玉", "numerology": "2", "color": "橙红"},
    24: {"element": "火", "astrology": "白羊", "chakra": "太阳神经丛", "crystal": "黄铁矿", "numerology": "3", "color": "金"},
    25: {"element": "火", "astrology": "白羊", "chakra": "心轮", "crystal": "石榴石", "numerology": "4", "color": "红"},
    26: {"element": "火", "astrology": "狮子", "chakra": "太阳神经丛", "crystal": "虎眼石", "numerology": "5", "color": "金棕"},
    27: {"element": "火", "astrology": "狮子", "chakra": "太阳神经丛", "crystal": "太阳石", "numerology": "6", "color": "金"},
    28: {"element": "火", "astrology": "狮子", "chakra": "太阳神经丛", "crystal": "红发晶", "numerology": "7", "color": "红"},
    29: {"element": "火", "astrology": "射手", "chakra": "太阳神经丛", "crystal": "蓝砂石", "numerology": "8", "color": "深蓝"},
    30: {"element": "火", "astrology": "射手", "chakra": "太阳神经丛", "crystal": "烟晶", "numerology": "9", "color": "棕"},
    31: {"element": "火", "astrology": "射手", "chakra": "海底轮", "crystal": "黑曜石", "numerology": "10", "color": "暗红"},
    32: {"element": "火", "astrology": "白羊", "chakra": "太阳神经丛", "crystal": "红玛瑙", "numerology": "Page", "color": "橙"},
    33: {"element": "火", "astrology": "狮子", "chakra": "太阳神经丛", "crystal": "红碧玉", "numerology": "Knight", "color": "红"},
    34: {"element": "火", "astrology": "狮子", "chakra": "心轮", "crystal": "太阳石", "numerology": "Queen", "color": "金"},
    35: {"element": "火", "astrology": "狮子", "chakra": "太阳神经丛", "crystal": "黄水晶", "numerology": "King", "color": "金"},

    # ── Cups (Water) ──────────────────────────────────────────────
    36: {"element": "水", "astrology": "巨蟹/天蝎/双鱼", "chakra": "心轮", "crystal": "粉晶", "numerology": "Ace", "color": "粉"},
    37: {"element": "水", "astrology": "巨蟹", "chakra": "心轮", "crystal": "月光石", "numerology": "2", "color": "银白"},
    38: {"element": "水", "astrology": "巨蟹", "chakra": "脐轮", "crystal": "海蓝宝", "numerology": "3", "color": "蓝"},
    39: {"element": "水", "astrology": "巨蟹", "chakra": "心轮", "crystal": "紫水晶", "numerology": "4", "color": "紫"},
    40: {"element": "水", "astrology": "天蝎", "chakra": "心轮", "crystal": "黑曜石", "numerology": "5", "color": "深蓝"},
    41: {"element": "水", "astrology": "天蝎", "chakra": "脐轮", "crystal": "月光石", "numerology": "6", "color": "银"},
    42: {"element": "水", "astrology": "天蝎", "chakra": "第三眼", "crystal": "紫水晶", "numerology": "7", "color": "靛"},
    43: {"element": "水", "astrology": "双鱼", "chakra": "心轮", "crystal": "海蓝宝", "numerology": "8", "color": "蓝"},
    44: {"element": "水", "astrology": "双鱼", "chakra": "顶轮", "crystal": "白水晶", "numerology": "9", "color": "白"},
    45: {"element": "水", "astrology": "双鱼", "chakra": "心轮", "crystal": "祖母绿", "numerology": "10", "color": "翠绿"},
    46: {"element": "水", "astrology": "巨蟹", "chakra": "第三眼", "crystal": "月光石", "numerology": "Page", "color": "银白"},
    47: {"element": "水", "astrology": "天蝎", "chakra": "心轮", "crystal": "粉晶", "numerology": "Knight", "color": "粉"},
    48: {"element": "水", "astrology": "天蝎", "chakra": "心轮", "crystal": "海蓝宝", "numerology": "Queen", "color": "蓝"},
    49: {"element": "水", "astrology": "双鱼", "chakra": "心轮", "crystal": "蓝砂石", "numerology": "King", "color": "深蓝"},

    # ── Swords (Air) ──────────────────────────────────────────────
    50: {"element": "风", "astrology": "双子/天秤/水瓶", "chakra": "喉轮", "crystal": "蓝玉髓", "numerology": "Ace", "color": "天蓝"},
    51: {"element": "风", "astrology": "天秤", "chakra": "第三眼", "crystal": "青金石", "numerology": "2", "color": "深蓝"},
    52: {"element": "风", "astrology": "天秤", "chakra": "心轮", "crystal": "黑曜石", "numerology": "3", "color": "灰"},
    53: {"element": "风", "astrology": "天秤", "chakra": "顶轮", "crystal": "紫水晶", "numerology": "4", "color": "紫"},
    54: {"element": "风", "astrology": "水瓶", "chakra": "太阳神经丛", "crystal": "黄铁矿", "numerology": "5", "color": "金"},
    55: {"element": "风", "astrology": "水瓶", "chakra": "第三眼", "crystal": "海蓝宝", "numerology": "6", "color": "蓝"},
    56: {"element": "风", "astrology": "水瓶", "chakra": "喉轮", "crystal": "蓝晶石", "numerology": "7", "color": "靛蓝"},
    57: {"element": "风", "astrology": "双子", "chakra": "第三眼", "crystal": "紫水晶", "numerology": "8", "color": "紫"},
    58: {"element": "风", "astrology": "双子", "chakra": "顶轮", "crystal": "白水晶", "numerology": "9", "color": "银"},
    59: {"element": "风", "astrology": "双子", "chakra": "海底轮", "crystal": "黑曜石", "numerology": "10", "color": "黑"},
    60: {"element": "风", "astrology": "双子", "chakra": "喉轮", "crystal": "蓝玉髓", "numerology": "Page", "color": "天蓝"},
    61: {"element": "风", "astrology": "双子", "chakra": "太阳神经丛", "crystal": "黄水晶", "numerology": "Knight", "color": "黄"},
    62: {"element": "风", "astrology": "天秤", "chakra": "喉轮", "crystal": "青金石", "numerology": "Queen", "color": "深蓝"},
    63: {"element": "风", "astrology": "水瓶", "chakra": "太阳神经丛", "crystal": "蓝玉髓", "numerology": "King", "color": "天蓝"},

    # ── Pentacles (Earth) ─────────────────────────────────────────
    64: {"element": "土", "astrology": "金牛/处女/摩羯", "chakra": "海底轮", "crystal": "祖母绿", "numerology": "Ace", "color": "翠绿"},
    65: {"element": "土", "astrology": "处女", "chakra": "海底轮", "crystal": "橄榄石", "numerology": "2", "color": "绿"},
    66: {"element": "土", "astrology": "摩羯", "chakra": "太阳神经丛", "crystal": "黄铁矿", "numerology": "3", "color": "金"},
    67: {"element": "土", "astrology": "摩羯", "chakra": "海底轮", "crystal": "黑碧玺", "numerology": "4", "color": "黑棕"},
    68: {"element": "土", "astrology": "金牛", "chakra": "海底轮", "crystal": "石榴石", "numerology": "5", "color": "暗红"},
    69: {"element": "土", "astrology": "金牛", "chakra": "心轮", "crystal": "粉晶", "numerology": "6", "color": "粉绿"},
    70: {"element": "土", "astrology": "金牛", "chakra": "海底轮", "crystal": "橄榄石", "numerology": "7", "color": "绿"},
    71: {"element": "土", "astrology": "处女", "chakra": "太阳神经丛", "crystal": "黄水晶", "numerology": "8", "color": "金"},
    72: {"element": "土", "astrology": "处女", "chakra": "心轮", "crystal": "祖母绿", "numerology": "9", "color": "翠绿"},
    73: {"element": "土", "astrology": "摩羯", "chakra": "海底轮", "crystal": "烟晶", "numerology": "10", "color": "棕"},
    74: {"element": "土", "astrology": "摩羯", "chakra": "海底轮", "crystal": "苔玛瑙", "numerology": "Page", "color": "绿棕"},
    75: {"element": "土", "astrology": "金牛", "chakra": "海底轮", "crystal": "橄榄石", "numerology": "Knight", "color": "绿"},
    76: {"element": "土", "astrology": "处女", "chakra": "心轮", "crystal": "祖母绿", "numerology": "Queen", "color": "翠绿"},
    77: {"element": "土", "astrology": "摩羯", "chakra": "太阳神经丛", "crystal": "黄水晶", "numerology": "King", "color": "金棕"},
}


def get_esoterica(card_id: int) -> dict:
    """Get esoteric associations for a card. Returns empty dict if not found."""
    return CARD_ESOTERICA.get(card_id, {})


def format_esoterica_for_prompt(card_id: int) -> str:
    """Format esoteric associations as a string for LLM prompt injection."""
    e = CARD_ESOTERICA.get(card_id, {})
    if not e:
        return ""
    parts = []
    if e.get("element"):
        parts.append(f"元素: {e['element']}")
    if e.get("astrology"):
        parts.append(f"星座: {e['astrology']}")
    if e.get("crystal"):
        parts.append(f"水晶: {e['crystal']}")
    if e.get("chakra"):
        parts.append(f"脉轮: {e['chakra']}")
    if e.get("numerology"):
        parts.append(f"数字灵义: {e['numerology']}")
    if e.get("color"):
        parts.append(f"色彩: {e['color']}")
    return " | ".join(parts)
