"""
Tarot drawing engine — Fisher-Yates shuffle, spread assignment, card formatting.
"""
import random
from typing import Optional

from .tarot_data import DECK, SPREAD_SIZES, SPREAD_POSITIONS
from .tarot_esoterica import format_esoterica_for_prompt


def draw_cards(spread: str = "three_card", rng: Optional[random.Random] = None) -> list[dict]:
    r = rng or random.Random()
    count = SPREAD_SIZES.get(spread, 3)
    positions = SPREAD_POSITIONS.get(spread, [f"位置{i}" for i in range(count)])

    pool = list(DECK.keys())
    r.shuffle(pool)
    drawn_ids = pool[:count]

    result = []
    for i, card_id in enumerate(drawn_ids):
        card = DECK[card_id].copy()
        card["reversed"] = r.random() < 0.5
        card["position"] = positions[i] if i < len(positions) else f"位置{i}"
        result.append(card)
    return result


def format_cards_for_llm(cards: list[dict]) -> str:
    lines = []
    for c in cards:
        orientation = "逆位" if c["reversed"] else "正位"
        keyword = c["keyword_reversed"] if c["reversed"] else c["keyword_upright"]
        desc = c["desc_reversed"] if c["reversed"] else c["desc_upright"]
        esoterica = format_esoterica_for_prompt(c["id"])
        lines.append(
            f"  [{c['position']}] {c['name_cn']}（{c['name_en']}）{orientation}\n"
            f"    关键词：{keyword}\n"
            f"    牌意：{desc}\n"
            f"    爱情指引：{c['love']}\n"
            f"    事业指引：{c['career']}\n"
            f"    健康指引：{c['health']}\n"
            f"    神秘学对应：{esoterica}"
        )
    return "\n".join(lines)


def cards_to_json(cards: list[dict]) -> list[dict]:
    from .tarot_esoterica import get_esoterica
    return [
        {
            "name": c["name_en"],
            "name_cn": c["name_cn"],
            "suit": c.get("suit"),
            "reversed": c["reversed"],
            "position": c["position"],
            "keyword": c["keyword_reversed"] if c["reversed"] else c["keyword_upright"],
            "description": c["desc_reversed"] if c["reversed"] else c["desc_upright"],
            "love": c["love"],
            "career": c["career"],
            "health": c["health"],
            "esoterica": get_esoterica(c["id"]),
        }
        for c in cards
    ]
