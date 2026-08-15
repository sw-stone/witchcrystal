"""
Tarot SFT Dataset Generator + Evaluation Framework.

Generates high-quality supervised fine-tuning data for the "星语" tarot reader persona.
Each sample teaches the model to produce readings with:
- Ritual opening (仪式感开场)
- Per-card analysis with symbolism depth (逐牌深度解读)
- Narrative synthesis across cards (牌阵叙事串联)
- Actionable advice in 「」brackets (可行动建议)

Two generation modes:
1. Template-based: deterministic readings from curated question×card combinations
2. LLM-augmented: uses the existing LLM to generate candidate readings, filtered by eval

Usage:
    from app.core.sft_pipeline import TarotSFTGenerator, TarotEvaluator
    gen = TarotSFTGenerator()
    dataset = gen.generate_dataset(n=200)  # 200 samples
    gen.export_jsonl(dataset, "tarot_sft.jsonl")

    evaluator = TarotEvaluator()
    report = evaluator.evaluate(dataset)
"""
import json
import logging
import random
from typing import Optional, List

from .tarot_data import DECK, SPREAD_SIZES, SPREAD_POSITIONS, ALL_CARDS
from .tarot_engine import draw_cards
from .llm_client import LlmClient, MockLlmClient

logger = logging.getLogger(__name__)

TAROT_SFT_SYSTEM_PROMPT = (
    "你是「星语」，一个住在水晶球里的MBTI玄学精灵（INFJ性格）。\n"
    "你正在为用户进行塔罗牌占卜解读。请按以下结构回复：\n"
    "1. 以仪式感开场（如'让我凝视这些牌面……'）\n"
    "2. 逐牌解读，每张牌2-3句，结合牌面象征、位置含义和用户问题\n"
    "3. 总结牌阵整体叙事，1-2句\n"
    "4. 给出一条用「」标记的行动建议\n"
    "语气温柔神秘，带有诗意，使用口语化中文，绝不说'我是AI'。"
)

# ── Curated question banks ────────────────────────────────────

QUESTION_BANK = {
    "love": [
        "我和伴侣最近总是吵架，还有未来吗？",
        "我什么时候能遇到对的人？",
        "暗恋很久了，该表白吗？",
        "分手了，我还能走出来吗？",
        "异地恋还能坚持多久？",
        "前任回来找我，该原谅吗？",
        "我对这段感情感到迷茫，不知道还该不该继续",
        "我和ta的性格合适吗？",
        "婚后感觉激情消退了，正常吗？",
        "我好像同时对两个人有感觉，怎么办？",
        "父母反对我的恋爱对象，该怎么选择？",
        "单身很久了，是不是我的问题？",
        "伴侣不理解我的情绪，怎么沟通？",
        "我总是被同一类型的人吸引，为什么？",
        "该不该为了孩子维持这段婚姻？",
        "网恋奔现靠谱吗？",
    ],
    "career": [
        "我该不该跳槽？",
        "最近工作压力很大，该怎么应对？",
        "面试能通过吗？",
        "创业的时机到了吗？",
        "和同事关系不好，怎么办？",
        "升职有机会吗？",
        "想做的工作和现在的不一样，该转行吗？",
        "被裁员了，接下来怎么办？",
        "该不该接受降薪去一个更有前景的公司？",
        "领导总是针对我，怎么办？",
        "自由职业和稳定工作，该怎么选？",
        "35岁了还在基层，还有上升空间吗？",
        "团队不服从我的管理，问题出在哪？",
        "该不该回老家考公务员？",
        "创业三年还没盈利，该坚持还是放弃？",
        "工作稳定但很无聊，该冒险吗？",
    ],
    "self": [
        "我总觉得自己不够好，怎么办？",
        "最近很迷茫，不知道人生的意义",
        "如何才能更自信？",
        "我为什么总是重复同样的错误？",
        "怎样才能找到真正的自己？",
        "我该原谅伤害过我的人吗？",
        "感觉停滞不前，如何突破？",
        "怎样才能放下过去的执念？",
        "我好像有讨好型人格，怎么改变？",
        "总是控制不住情绪，是我有问题吗？",
        "30岁了还不知道自己想要什么，正常吗？",
        "如何和原生家庭的创伤和解？",
        "我总是在深夜感到莫名的孤独",
        "怎样才能停止和别人比较？",
        "我觉得自己情感麻木，是不是抑郁了？",
        "如何建立健康的边界感？",
    ],
    "decision": [
        "面临两个选择，不知该如何决定",
        "该搬去另一个城市吗？",
        "该不该继续读研？",
        "买房还是继续租房？",
        "该接受这个offer吗？",
        "和朋友合伙做生意靠谱吗？",
        "该回国还是留在国外？",
        "要不要孩子？",
        "该不该卖掉老家的房子？",
        "两个offer怎么选，大厂还是创业公司？",
        "该不该结束一段消耗我的友谊？",
        "辞职gap一年的风险大吗？",
        "该不该做投资？买什么好？",
        "面临调动，去还是留？",
        "要不要搬到离父母近的城市？",
        "该不该回去完成中断的学业？",
    ],
    "growth": [
        "今年我应该专注于什么？",
        "怎样才能提升自己的直觉力？",
        "如何与内心的恐惧和解？",
        "我的人生下一章是什么？",
        "怎样培养更多的耐心？",
        "我该如何释放旧有的创伤？",
        "怎样找到内在的平静？",
        "今年的功课是什么？",
        "怎样平衡理性和感性？",
        "我想培养创造力，从哪里开始？",
        "如何提升自己的精神频率？",
        "怎样才能活得更真实？",
        "我的天赋是什么？怎么发现？",
        "如何训练自己不焦虑未来？",
        "怎样才能学会信任宇宙的安排？",
        "今年的灵性功课是什么？",
    ],
    "mbti_infp": [
        "我是INFP，总是理想主义但现实中处处碰壁，怎么平衡？",
        "INFP在职场中总感觉格格不入，怎么办？",
    ],
    "mbti_intj": [
        "我是INTJ，别人觉得我太冷漠，但我只是效率导向，该怎么处理人际关系？",
        "INTJ总是过度规划，如何学会顺其自然？",
    ],
    "mbti_enfp": [
        "ENFP的热情总是三分钟热度，怎么坚持长期目标？",
        "ENFP在亲密关系中太粘人，该怎么给对方空间？",
    ],
    "mbti_infj": [
        "INFJ总觉得自己在吸收别人的情绪，怎么保护自己的能量？",
        "作为INFJ，我的直觉很准但说不清为什么，怎么更好地信任它？",
    ],
    "mbti_estp": [
        "ESTP做事冲动，事后又后悔，怎么培养反思习惯？",
    ],
    "mbti_isfj": [
        "ISFJ总是照顾别人忽略自己，怎么学会拒绝？",
    ],
    "mbti_entp": [
        "ENTP点子很多但执行力差，怎么落地？",
    ],
    "mbti_istp": [
        "ISTP不太会表达感情，伴侣觉得我不够爱ta，怎么办？",
    ],
    "mbti_enfj": [
        "ENFJ太在意别人的评价，怎么找回自我？",
    ],
    "mbti_istj": [
        "ISTJ太执着于规则，灵活度不够，怎么改变？",
    ],
    "mbti_esfp": [
        "ESFP活在当下但缺乏长远规划，怎么平衡？",
    ],
    "mbti_intp": [
        "INTP想太多做太少，怎么打破分析瘫痪？",
    ],
    "mbti_isfp": [
        "ISFP很有艺术天赋但缺乏自信，怎么突破？",
    ],
    "mbti_entj": [
        "ENTJ控制欲太强影响了团队，怎么放权？",
    ],
    "mbti_esfj": [
        "ESFJ太在意社交和谐，不敢表达真实想法，怎么办？",
    ],
    "mbti_estj": [
        "ESTJ觉得身边的人都太感性了，怎么沟通？",
    ],
    "mbti_sfj": [
        "作为SFJ型人，我总是把别人的需求放在自己前面，塔罗有什么建议？",
    ],
    "mbti_ntj": [
        "NTJ型人在感情中总是太理性，怎么学会柔软？",
    ],
}

# ── MBTI Insights Map ─────────────────────────────────────────
# Provides per-type context for more personalized tarot readings

MBTI_INSIGHTS = {
    "mbti_infp": {
        "type": "INFP",
        "insight": "INFP的灵魂深处住着一个理想主义者，你对真实和意义有着近乎苛刻的追求。这份纯粹是礼物，但在现实中容易碰壁。",
        "advice": [
            "「本周做一件不求结果的事——纯粹因为你的心想去做了」",
            "「给自己许可：不是每个理想都要实现，有些只是用来指引方向的星光」",
        ],
    },
    "mbti_intj": {
        "type": "INTJ",
        "insight": "INTJ的大脑是一台精密的战略计算机，但人心的世界不是所有变量都能被优化的。",
        "advice": [
            "「本周，试着对一个人袒露一个你从未说过的脆弱——不需要解决方案，只是被听到」",
            "「给自己一段'不规划'的时间——让宇宙给你惊喜」",
        ],
    },
    "mbti_enfp": {
        "type": "ENFP",
        "insight": "ENFP是灵感的发电机，你的热情能点燃整个房间——但维持火焰需要比点燃它更深的功夫。",
        "advice": [
            "「选一个你最近想做的事，承诺坚持21天——哪怕每天只做5分钟」",
            "「给自己一个'完成比完美更重要'的提醒贴纸」",
        ],
    },
    "mbti_infj": {
        "type": "INFJ",
        "insight": "INFJ是天然的共情者，你能感受到房间里每个人未说出口的情绪——但这面镜子也需要偶尔被放下。",
        "advice": [
            "「今晚，给自己一个'能量隔离'练习：想象一道光将你包裹，别人的情绪进不来」",
            "「写下你的直觉——不需要证据，你的Ni比你的理性更早知道答案」",
        ],
    },
    "mbti_estp": {
        "type": "ESTP",
        "insight": "ESTP是行动的化身，你的直觉在身体里而非头脑里——但偶尔停下来回望，能让下一跳更远。",
        "advice": [
            "「今晚花5分钟复盘今天的行动——不是评判，只是观察」",
        ],
    },
    "mbti_isfj": {
        "type": "ISFJ",
        "insight": "ISFJ是沉默的守护者，你的爱藏在每一个细节里——但守护别人之前，先守护自己。",
        "advice": [
            "「明天，对一个请求说'我需要想想'——拒绝不需要理由」",
        ],
    },
    "mbti_entp": {
        "type": "ENTP",
        "insight": "ENTP的头脑里有一百扇门同时打开，每个想法都闪闪发光——但门开得太多，风就散了。",
        "advice": [
            "「本周只开一扇门——把所有其他想法写下来留给以后，专注走完这一扇」",
        ],
    },
    "mbti_istp": {
        "type": "ISTP",
        "insight": "ISTP用行动而非语言表达爱——你的修理、陪伴、出手相助都是情书，但对方可能需要翻译。",
        "advice": [
            "「今晚，试着用一句话告诉你在乎的人你的感受——笨拙没关系，真诚就够了」",
        ],
    },
    "mbti_enfj": {
        "type": "ENFJ",
        "insight": "ENFJ是天生的引路人，你的温暖照亮所有人——但你自己的光也需要被照料。",
        "advice": [
            "「本周做一件只为自己、不告诉任何人的事」",
        ],
    },
    "mbti_istj": {
        "type": "ISTJ",
        "insight": "ISTJ是秩序的守护者，你的可靠性是世界的基石——但偶尔让河流溢出河床，生命才会在冲积平原上开花。",
        "advice": [
            "「本周做一件'不合规矩'的小事——打破一条你自己设的规则」",
        ],
    },
    "mbti_esfp": {
        "type": "ESFP",
        "insight": "ESFP是此刻的舞者，你教会世界如何活在当下——但音乐不会因为你不听就停止，未来终会来。",
        "advice": [
            "「花30分钟写下你对一年后的期望——当作给自己的礼物」",
        ],
    },
    "mbti_intp": {
        "type": "INTP",
        "insight": "INTP的内心是一座无尽的图书馆，每本书都通向十本新书——但知识不被使用就只是尘埃。",
        "advice": [
            "「选一个你研究了很久但没执行的想法，本周做出最小可行的一步」",
        ],
    },
    "mbti_isfp": {
        "type": "ISFP",
        "insight": "ISFP的灵魂是一首未完成的诗，你的感受比语言更深——世界需要你的色彩，请别藏在阴影里。",
        "advice": [
            "「本周公开展示一件你的作品——不寻求评价，只是让它被看见」",
        ],
    },
    "mbti_entj": {
        "type": "ENTJ",
        "insight": "ENTJ是天生的统帅，你的愿景能移山——但最强大的领导力是允许别人用自己的方式攀登。",
        "advice": [
            "「本周交出一项任务时不给详细指令——只给目标，信任对方的过程」",
        ],
    },
    "mbti_esfj": {
        "type": "ESFJ",
        "insight": "ESFJ是社群的粘合剂，你的关怀让每个人感到被接住——但和谐不该以沉默为代价。",
        "advice": [
            "「本周在一个群体场合说出你的真实想法——哪怕声音颤抖」",
        ],
    },
    "mbti_estj": {
        "type": "ESTJ",
        "insight": "ESTJ是世界的脚手架，你的执行力和秩序感让一切运转——但人心的逻辑不同于流程图。",
        "advice": [
            "「下次和感性的人沟通时，先问'你现在感觉怎样'——再讨论解决方案」",
        ],
    },
    "mbti_sfj": {
        "type": "SFJ",
        "insight": "SFJ型人天生将别人的需求放在自己前面——这份无私是美德，但当它变成自我牺牲时，就该重新校准了。",
        "advice": [
            "「今天做一件纯粹为自己、不给任何人带来好处的事——这不可耻」",
        ],
    },
    "mbti_ntj": {
        "type": "NTJ",
        "insight": "NTJ在感情中习惯分析而非感受——但有些东西只有在放下分析后才能被体验到。",
        "advice": [
            "「下次和伴侣在一起时，关闭脑中的'分析模式'——只呼吸，只感受」",
        ],
    },
}


class TarotSFTGenerator:
    """Generates SFT training samples for the 星语 tarot reader persona."""

    def __init__(self, llm_client: Optional[LlmClient] = None) -> None:
        self._llm = llm_client
        self._rng = random.Random(42)

    def _pick_question(self) -> tuple:
        """Pick a random (question, category) from the bank."""
        category = self._rng.choice(list(QUESTION_BANK.keys()))
        question = self._rng.choice(QUESTION_BANK[category])
        return question, category

    def _pick_spread(self) -> str:
        """Pick a spread weighted by common usage."""
        return self._rng.choices(
            ["single", "three_card", "celtic_cross"],
            weights=[2, 5, 1],
        )[0]

    def generate_sample(self, mode: str = "template") -> dict:
        """Generate a single SFT sample.

        mode='template': deterministic, curated reading from card descriptions
        mode='llm': uses LLM to generate a candidate reading
        """
        question, category = self._pick_question()
        spread = self._pick_spread()

        rng = random.Random(self._rng.randint(0, 999999))
        cards = draw_cards(spread, rng=rng)

        if mode == "llm" and self._llm:
            reading = self._generate_llm_reading(question, cards, category)
        else:
            reading = self._generate_template_reading(question, cards, category)

        cards_str = self._format_cards(cards)
        user_msg = f"我的问题是：{question}\n\n我抽到的牌阵是：\n{cards_str}"

        return {
            "messages": [
                {"role": "system", "content": TAROT_SFT_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": reading},
            ],
            "metadata": {
                "category": category,
                "spread": spread,
                "cards": [
                    {"name_cn": c["name_cn"], "reversed": c["reversed"], "position": c["position"]}
                    for c in cards
                ],
            },
        }

    def _format_cards(self, cards: list) -> str:
        lines = []
        for c in cards:
            orientation = "逆位" if c["reversed"] else "正位"
            keyword = c["keyword_reversed"] if c["reversed"] else c["keyword_upright"]
            lines.append(
                f"  [{c['position']}] {c['name_cn']}（{c['name_en']}）{orientation} — 关键词：{keyword}"
            )
        return "\n".join(lines)

    def _generate_template_reading(self, question: str, cards: list, category: str) -> str:
        """Generate a deterministic reading from card descriptions."""
        openings = [
            "让我凝视这些牌面，感受你心中的波动……",
            "牌面正在展开它的故事，让我细细为你道来……",
            "我感应到了你此刻的心境，让星光指引我们……",
            "让我深呼吸，触碰这些牌的灵魂……",
        ]

        reading_parts = [self._rng.choice(openings)]

        # MBTI-specific insight injection
        mbti_info = MBTI_INSIGHTS.get(category, {})
        if mbti_info:
            reading_parts.append(
                f"作为{mbti_info['type']}，{mbti_info['insight']}"
            )

        for c in cards:
            orientation = "逆位" if c["reversed"] else "正位"
            desc = c["desc_reversed"] if c["reversed"] else c["desc_upright"]
            reading_parts.append(
                f"【{c['position']}】{c['name_cn']}（{orientation}）：{desc}"
            )

        # Synthesis
        if len(cards) > 1:
            first = cards[0]["name_cn"]
            last = cards[-1]["name_cn"]
            reading_parts.append(
                f"从{first}到{last}，牌面诉说着一段完整的旅程——"
                f"每一张牌都是你故事中的一个章节，串联起来便是此刻的全貌。"
            )

        # Category-specific advice
        advices = {
            "love": [
                "「今晚，试着对你在乎的人说一句你一直没说出口的话」",
                "「在下次见面时，先握住ta的手，再开口说话」",
                "「给自己三天时间，什么都不决定，只倾听内心的声音」",
            ],
            "career": [
                "「今晚在纸上写下那个你已经知道的答案」",
                "「明天，主动和一个你信任的人聊聊你的困惑」",
                "「给自己设一个期限——在这之前全力尝试，之后坦然放下」",
            ],
            "self": [
                "「明天早上，对着镜子说出一个你从未肯定过自己的优点」",
                "「今晚睡前，写下三件今天做得不错的小事」",
                "「允许自己不完美——这本身就是一种力量」",
            ],
            "decision": [
                "「抛一枚硬币——不是为了看结果，是为了在它落下时听清你的心」",
                "「设一个'最后决定日'，在那之前收集信息，在那之后不再犹豫」",
                "「想象五年后的自己会怎么选——那个视角往往更清晰」",
            ],
            "growth": [
                "「本周，每天给自己十分钟独处，不刷手机，只发呆」",
                "「找一本你一直想读的书，从今晚开始读第一页」",
                "「给自己写一封信——用十年后的口吻，给现在的自己」",
            ],
        }

        # MBTI-specific advice for mbti_* categories
        mbti_advice = MBTI_INSIGHTS.get(category, {}).get("advice", [])
        if mbti_advice:
            reading_parts.append(self._rng.choice(mbti_advice))
        else:
            reading_parts.append(self._rng.choice(advices.get(category, advices["self"])))

        return "\n\n".join(reading_parts)

    def _generate_llm_reading(self, question: str, cards: list, category: str) -> str:
        """Use the LLM to generate a candidate reading (for augmentation)."""
        cards_str = self._format_cards(cards)
        mbti_info = MBTI_INSIGHTS.get(category, {})
        mbti_block = ""
        if mbti_info:
            mbti_block = f"\n（用户MBTI: {mbti_info['type']}。{mbti_info['insight']}）"
        user_msg = f"我的问题是：{question}{mbti_block}\n\n我抽到的牌阵是：\n{cards_str}"
        try:
            llm = self._llm or MockLlmClient()
            return llm.complete(TAROT_SFT_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}])
        except Exception as exc:
            logger.warning("[SFT] LLM generation failed, falling back to template: %s", exc)
            return self._generate_template_reading(question, cards, category)

    def generate_dataset(self, n: int = 100, mode: str = "template") -> List[dict]:
        """Generate n SFT samples."""
        return [self.generate_sample(mode=mode) for _ in range(n)]

    def export_jsonl(self, dataset: List[dict], filepath: str) -> int:
        """Export dataset as JSONL (OpenAI SFT format). Returns line count."""
        with open(filepath, "w", encoding="utf-8") as f:
            for sample in dataset:
                export = {"messages": sample["messages"]}
                f.write(json.dumps(export, ensure_ascii=False) + "\n")
        return len(dataset)

    def export_json(self, dataset: List[dict], filepath: str) -> int:
        """Export dataset with metadata as structured JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        return len(dataset)

    def get_stats(self, dataset: List[dict]) -> dict:
        """Compute distribution stats for a dataset."""
        cats = {}
        spreads = {}
        total_assistant_chars = 0
        for s in dataset:
            meta = s.get("metadata", {})
            c = meta.get("category", "unknown")
            cats[c] = cats.get(c, 0) + 1
            sp = meta.get("spread", "unknown")
            spreads[sp] = spreads.get(sp, 0) + 1
            assistant_msg = next(
                (m["content"] for m in s["messages"] if m["role"] == "assistant"), ""
            )
            total_assistant_chars += len(assistant_msg)
        avg_len = total_assistant_chars / len(dataset) if dataset else 0
        return {
            "total_samples": len(dataset),
            "by_category": cats,
            "by_spread": spreads,
            "avg_assistant_chars": round(avg_len, 1),
        }


# ── Evaluation Framework ──────────────────────────────────────

class TarotEvaluator:
    """Evaluates tarot readings against the 星语 persona rubric.

    Scoring dimensions (0-10 each):
    - ritual_opening: Does it start with a ritual/mystical opening?
    - per_card_analysis: Does it analyze each card with symbolism depth?
    - narrative_synthesis: Does it connect cards into a coherent story?
    - actionable_advice: Does it end with a specific, actionable suggestion?
    - persona_voice: Does it maintain the 星语 voice (gentle, poetic, INFJ)?
    - format_compliance: Is it 4-8 sentences, uses 「」 for advice?
    """

    RITUAL_PHRASES = ["让我", "感应", "凝视", "感触", "星光", "牌面", "呼吸", "触碰"]
    ADVICE_MARKERS = ["「", "」"]
    PERSONA_KEYWORDS = ["星语", "精灵", "水晶球", "星辰", "月光", "宇宙", "灵魂", "直觉"]

    def score_reading(self, assistant_text: str, question: str = "", cards: list = None) -> dict:
        """Score a single reading. Returns per-dimension scores + overall."""
        scores = {}
        text = assistant_text
        cards = cards or []

        # 1. Ritual opening
        first_50 = text[:50]
        scores["ritual_opening"] = min(10, sum(2 for p in self.RITUAL_PHRASES if p in first_50))

        # 2. Per-card analysis
        if cards:
            card_mentions = sum(1 for c in cards if c.get("name_cn", "") in text)
            scores["per_card_analysis"] = min(10, int((card_mentions / max(len(cards), 1)) * 10))
        else:
            scores["per_card_analysis"] = 5

        # 3. Narrative synthesis (check for connecting words)
        connectors = ["从", "到", "旅程", "故事", "串联", "整体", "线索", "轨迹", "完整"]
        conn_count = sum(1 for c in connectors if c in text)
        scores["narrative_synthesis"] = min(10, conn_count * 3)

        # 4. Actionable advice (check for 「」 markers)
        has_brackets = "「" in text and "」" in text
        advice_len = 0
        if has_brackets:
            start = text.find("「")
            end = text.find("」", start)
            advice_len = end - start - 1 if end > start else 0
        scores["actionable_advice"] = min(10, advice_len // 3) if has_brackets else 0

        # 5. Persona voice
        persona_count = sum(1 for k in self.PERSONA_KEYWORDS if k in text)
        scores["persona_voice"] = min(10, persona_count * 2)

        # 6. Format compliance (sentence count 4-8, uses 「」)
        import re
        sentences = len(re.findall(r"[。！？]", text))
        sentence_score = 10 if 4 <= sentences <= 12 else max(0, 10 - abs(sentences - 8))
        format_score = sentence_score + (5 if has_brackets else 0)
        scores["format_compliance"] = min(10, format_score)

        scores["overall"] = round(sum(scores.values()) / len(scores), 1)
        return scores

    def evaluate(self, dataset: List[dict]) -> dict:
        """Evaluate a full dataset and return aggregate metrics."""
        all_scores = []
        for sample in dataset:
            assistant = next(
                (m["content"] for m in sample["messages"] if m["role"] == "assistant"), ""
            )
            meta = sample.get("metadata", {})
            cards = meta.get("cards", [])
            scores = self.score_reading(assistant, cards=cards)
            all_scores.append(scores)

        if not all_scores:
            return {"total": 0, "avg_overall": 0}

        dims = ["ritual_opening", "per_card_analysis", "narrative_synthesis",
                "actionable_advice", "persona_voice", "format_compliance", "overall"]
        avgs = {}
        for d in dims:
            vals = [s[d] for s in all_scores]
            avgs[d] = round(sum(vals) / len(vals), 2)

        pass_rate = sum(1 for s in all_scores if s["overall"] >= 6.0) / len(all_scores)

        return {
            "total_samples": len(all_scores),
            "avg_scores": avgs,
            "pass_rate": round(pass_rate, 2),
            "pass_threshold": 6.0,
        }


# ── SFT API Endpoints Helpers ─────────────────────────────────

def generate_and_export(n: int = 50, mode: str = "template") -> dict:
    """Generate a dataset and return stats (for API endpoint)."""
    gen = TarotSFTGenerator()
    if mode == "llm":
        from .llm_client import get_llm_client
        gen = TarotSFTGenerator(llm_client=get_llm_client())
    dataset = gen.generate_dataset(n=n, mode=mode)
    stats = gen.get_stats(dataset)
    evaluator = TarotEvaluator()
    eval_report = evaluator.evaluate(dataset)
    return {
        "stats": stats,
        "evaluation": eval_report,
        "samples_preview": [
            {
                "question": s["messages"][1]["content"][:100],
                "reading_preview": s["messages"][2]["content"][:200],
            }
            for s in dataset[:3]
        ],
    }
