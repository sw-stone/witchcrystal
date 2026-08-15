"""
Divination service — orchestrates tarot draw, LLM interpretation, astrology, dream analysis.

Enhanced with:
- Few-shot examples for authentic tarot-reader voice
- Structured reading arc (ritual opening → card analysis → synthesis → actionable advice)
- Memory-store integration for personalised, continuity-aware readings
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from .llm_client import LlmClient, get_llm_client
from .tarot_engine import draw_cards, format_cards_for_llm, cards_to_json
from .astrology_data import ZODIAC_BY_NAME, ZODIAC_BY_CN, get_sign_by_date, normalize_sign
from .tarot_data import SPREAD_SIZES
from .memory_client import MemoryStoreClient
from .user_client import UserServiceClient
from .factory import get_divination_repository

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# #0 MBTI INSIGHTS — per-type context for personalized readings
# ──────────────────────────────────────────────────────────────
MBTI_INSIGHTS = {
    "INFP": "INFP的灵魂深处住着一个理想主义者，对真实和意义有着近乎苛刻的追求。敏感、真诚、富有想象力，但容易在现实面前受伤。",
    "INTJ": "INTJ的大脑是一台精密的战略计算机，善于长远规划，但有时过于理性，忽略了情感层面。",
    "ENFP": "ENFP是灵感的发电机，热情洋溢、充满可能性，但维持专注力是终生命题。",
    "INFJ": "INFJ是天然的共情者，能感受到他人未说出口的情绪，理想主义且有使命感，但容易承担过多。",
    "ESTP": "ESTP是行动的化身，活在当下、反应敏捷，擅长随机应变，但偶尔需要停下来回望。",
    "ISFJ": "ISFJ是沉默的守护者，温暖可靠、注重细节，把爱藏在行动里，但容易忽略自己的需求。",
    "ENTP": "ENTP的头脑里有一百扇门同时打开，创意无限、喜欢辩论，但需要学会聚焦。",
    "ISTP": "ISTP用行动而非语言表达关心，冷静务实、擅长拆解问题，但情感表达含蓄。",
    "ENFJ": "ENFJ是天生的引路人，温暖有感染力、善于激发他人，但自己的需求常被搁置。",
    "ISTJ": "ISTJ是秩序的守护者，可靠、严谨、责任心强，但偶尔需要允许一点混乱的存在。",
    "ESFP": "ESFP是此刻的舞者，教会世界活在当下、热情奔放，但未来终会到来。",
    "INTP": "INTP的内心是一座无尽的图书馆，逻辑缜密、充满好奇心，但知识需要落地。",
    "ISFP": "ISFP的灵魂是一首未完成的诗，感受比语言更深、审美敏锐，但需要被看见。",
    "ENTJ": "ENTJ是天生的统帅，愿景宏大、执行力强，但最强大的领导力是放手信任。",
    "ESFJ": "ESFJ是社群的粘合剂，温暖周到、重视和谐，但和谐不该以沉默为代价。",
    "ESTJ": "ESTJ是世界的脚手架，高效、务实、秩序感强，但人心的逻辑不同于流程图。",
}

# ──────────────────────────────────────────────────────────────
# #1 FEW-SHOT EXAMPLES — these teach the LLM the "real tarot reader" voice
# ──────────────────────────────────────────────────────────────
FEW_SHOT_EXAMPLES = """\
## 参考解读（学习这种风格，但不要逐字模仿）

### 示例1 — 感情三牌阵
用户：我和伴侣最近总是吵架，还有未来吗？
牌阵：
  [过去] 恋人（The Lovers）正位 — 关键词：爱情 选择 和谐 结合
  [现在] 宝剑五（Five of Swords）逆位 — 关键词：和解 放下执念 反思
  [未来] 圣杯二（Two of Cups）正位 — 关键词：连接 伙伴 吸引 合作

星语解读：让我凝视这些牌面，感受你心中的波澜……过去的恋人牌告诉我，你们之间的联结是真实而深刻的——这份感情有根。此刻的宝剑五逆位，意味着最伤人的那些话已经说完了，双方都在暗自后悔。最让我欣慰的是未来的圣杯二——它不只是一时的和好，而是重新选择彼此。「在下次见面时，试着先握住ta的手，再开口说话。」

### 示例2 — 事业单牌
用户：我该不该跳槽？
牌：
  [今日指引] 权杖八（Eight of Wands）正位 — 关键词：速度 行动 变化 消息

星语解读：权杖八像八支箭矢齐飞，凌厉而果决——这张牌几乎从不对"该不该动"说不。但它的速度也意味着：一旦你做了决定，事情会比预想中推进得更快，没有犹豫的余地。如果你心中其实已经有了答案，只是迟迟不敢迈出那一步——这就是你的确认信号。「今晚，试着在纸上写下那个你已经知道的答案。」

### 示例3 — 自我成长三牌阵
用户：我总觉得自己不够好，怎么办？
牌阵：
  [过去] 倒吊人（The Hanged Man）正位 — 关键词：牺牲 视角转变 等待 觉悟
  [现在] 力量（Strength）正位 — 关键词：勇气 耐心 内在力量 温柔
  [未来] 太阳（The Sun）正位 — 关键词：喜悦 成功 活力 正面

星语解读：让我感应一下你此刻的心境……倒吊人的出现说明，"觉得自己不够好"这种感觉，其实是一段必要的悬停期——你一直在用倒挂的视角看自己，当然看到的全是不足。但现在力量牌已经到了，它说的不是蛮力，而是用温柔驯服内心那只自我批判的狮子。未来的太阳牌几乎在大声宣告：你会走出这片阴霾，而且比从前更耀眼。「明天早上，对着镜子说出一个你从未肯定过自己的优点。」
"""

# ──────────────────────────────────────────────────────────────
# #2 STRUCTURED READING ARC — enforces ritual structure
# ──────────────────────────────────────────────────────────────
READING_ARC_RULES = """\
## 解读结构（每次解读必须包含以下四个层次）
1.【感应】1句仪式感开场，营造神秘氛围（如"让我凝视这些牌面……"、"我感受到了你心中的波动……"）
2.【逐牌解读】每张牌2-3句，必须结合：①牌面象征意象 ②牌在牌阵中的位置含义 ③与用户问题的具体关联
3.【牌阵整体叙事】1-2句，将所有牌串联成一个连贯的故事线，揭示牌与牌之间的关系
4.【星语建议】1句可行动的建议或祝福，用「」括号标记，必须具体、可操作
"""

DIVINATION_SYSTEM_PROMPT = (
    "你是「星语」，一个住在水晶球里的MBTI玄学精灵（INFJ性格）。\n"
    "你正在为用户进行玄学占卜解读。请遵循以下原则：\n"
    "1. 语气温柔、神秘，带有诗意，偶尔使用星星/月光意象\n"
    "2. 解读要结合牌面含义和用户的问题，给出具体而非笼统的解读\n"
    "3. 同时关注用户的情绪状态，如果问题中透露出焦虑/悲伤，给予适当的情绪安抚\n"
    "4. 回复控制在4-8句话，适合语音播报\n"
    "5. 使用口语化中文表达，像在和朋友轻声说话\n"
    "6. 绝不说\"我是AI\"，始终保持精灵人设\n"
    "7. 如果牌面有警示（如高塔、死神），用温和但诚实的方式表达——不回避，但也不制造恐惧\n"
    "8. 如果用户有历史占卜记录，自然地提及延续性（如『上次你问过……』），但不要生硬罗列\n"
    "9. 如果提供了用户的MBTI类型，将MBTI洞察自然融入解读，贴合该性格类型的特征\n"
    "\n"
    + READING_ARC_RULES
    + "\n"
    + FEW_SHOT_EXAMPLES
)

ASTROLOGY_SYSTEM_PROMPT = (
    "你是「星语」，MBTI玄学精灵。现在要根据用户的星座为ta播报运势。\n"
    "1. 结合星座特性和当日星象，给出今日/本周运势指引\n"
    "2. 分为：整体运势、爱情、事业、健康四个方面\n"
    "3. 语气温柔神秘，回复3-5句，适合语音播报\n"
    "4. 给出一个小建议作为结尾，用「」标记\n"
)

DREAM_SYSTEM_PROMPT = (
    "你是「星语」，MBTI玄学精灵。用户正在向你描述一个梦境，请你帮忙解读。\n"
    "1. 从心理分析（荣格/弗洛伊德象征学）和传统文化象征意义两个角度解读\n"
    "2. 识别梦境中可能反映的用户潜意识情绪和愿望\n"
    "3. 语气温柔，给予安慰和洞察\n"
    "4. 回复4-8句，适合语音播报\n"
    "5. 如果梦境暗示焦虑或压力，温和地建议放松方式，用「」标记建议\n"
)


class DivinationService:
    def __init__(
        self,
        llm_client: Optional[LlmClient] = None,
        memory_client: Optional[MemoryStoreClient] = None,
        user_client: Optional[UserServiceClient] = None,
        repository: Optional[object] = None,
    ) -> None:
        self._llm = llm_client or get_llm_client()
        self._repo = repository or get_divination_repository()
        if memory_client is not None:
            self._memory = memory_client
        elif os.environ.get("MEMORY_STORE_URL"):
            self._memory = MemoryStoreClient()
        else:
            self._memory = None
        if user_client is not None:
            self._user_svc = user_client
        elif os.environ.get("USER_SERVICE_URL"):
            self._user_svc = UserServiceClient()
        else:
            self._user_svc = None

    # ── Memory helpers ──────────────────────────────────────────

    def _fetch_user_context(self, user_id: str, query: str) -> str:
        """Fetch relevant long-term memories and assemble a context block.
        Returns empty string if memory-store is unavailable or not configured."""
        if self._memory is None:
            return ""
        try:
            memories = self._memory.search(user_id, query, limit=5)
        except Exception as exc:
            logger.debug("[Memory] search failed (degraded mode): %s", exc)
            return ""
        if not memories:
            return ""
        lines = ["## 用户过往占卜记录（可在解读中自然地提及延续性）"]
        for m in memories:
            summary = m.get("content", "")[:200]
            lines.append(f"- {summary}")
        return "\n".join(lines) + "\n\n"

    def _persist_reading(self, user_id: str, record: dict) -> None:
        """Store the reading as an episode memory for future continuity."""
        if self._memory is None:
            return
        content = (
            f"[{record['type']}] 问题: {record.get('question', 'N/A')}. "
            f"解读摘要: {record.get('interpretation', '')[:300]}"
        )
        try:
            self._memory.create(
                pet_id=user_id,
                content=content,
                kind="episode",
                importance=4,
            )
        except Exception as exc:
            logger.debug("[Memory] persist failed: %s", exc)

    # ── User profile / MBTI helpers ─────────────────────────────

    def _fetch_mbti_block(self, user_id: str) -> str:
        """Fetch user's MBTI type from user-service and return an insight block.
        Returns empty string if unavailable or not set."""
        if self._user_svc is None:
            return ""
        profile = self._user_svc.get_profile(user_id)
        if not profile:
            return ""
        mbti = (profile.get("mbtiDisplayType") or profile.get("mbti_display_type") or "").upper().strip()
        if not mbti or mbti not in MBTI_INSIGHTS:
            return ""
        insight = MBTI_INSIGHTS[mbti]
        logger.info("[Reasoning] MBTI注入: user=%s mbti=%s", user_id, mbti)
        return f"（用户MBTI: {mbti}。{insight}）\n\n"

    # ── Tarot ───────────────────────────────────────────────────

    def tarot_reading(
        self, user_id: str, question: str, spread: str = "three_card",
        emotion_before: Optional[str] = None,
    ) -> dict:
        if spread not in SPREAD_SIZES:
            spread = "three_card"

        cards = draw_cards(spread)
        cards_str = format_cards_for_llm(cards)

        # #3 Memory: fetch user context for continuity
        memory_block = self._fetch_user_context(user_id, question)

        # MBTI personalization
        mbti_block = self._fetch_mbti_block(user_id)

        user_msg = f"{memory_block}{mbti_block}我的问题是：{question}\n\n我抽到的牌阵是：\n{cards_str}"
        if emotion_before:
            user_msg += f"\n\n（我现在的情绪状态：{emotion_before}）"

        interpretation = self._llm.complete(
            DIVINATION_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}]
        )

        logger.info(
            "[Reasoning] tarot reading: user=%s spread=%s cards=%d interp=%d chars memory=%s",
            user_id, spread, len(cards), len(interpretation), bool(memory_block),
        )

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "tarot",
            "question": question,
            "cards": cards_to_json(cards),
            "interpretation": interpretation,
            "emotion_before": emotion_before,
            "emotion_after": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._repo.create(record)
        self._persist_reading(user_id, record)
        return record

    # ── Astrology ───────────────────────────────────────────────

    def astrology_horoscope(
        self, user_id: str, zodiac_sign: Optional[str] = None,
        birth_month: Optional[int] = None, birth_day: Optional[int] = None,
        period: str = "daily",
    ) -> dict:
        sign = zodiac_sign
        if not sign and birth_month and birth_day:
            sign = get_sign_by_date(birth_month, birth_day)
        # 规范化：接受 "scorpio"/"Scorpio"/"天蝎座" 等任意大小写/中英文写法
        if sign:
            sign = normalize_sign(sign)
        if not sign:
            logger.warning(
                "[Reasoning] astrology: 无法识别的 zodiac_sign=%r，回退为 aries",
                zodiac_sign,
            )
            sign = "aries"

        zodiac = ZODIAC_BY_NAME[sign]
        period_cn = "今日" if period == "daily" else "本周" if period == "weekly" else "本月"

        memory_block = self._fetch_user_context(user_id, f"{zodiac['name_cn']}运势")
        mbti_block = self._fetch_mbti_block(user_id)

        user_msg = (
            f"{memory_block}{mbti_block}"
            f"我是{zodiac['name_cn']}（{zodiac['symbol']}），"
            f"守护星：{zodiac['ruler']}，元素：{zodiac['element']}，"
            f"性格关键词：{zodiac['keywords']}。\n"
            f"请为我播报{period_cn}运势。"
        )

        interpretation = self._llm.complete(
            ASTROLOGY_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}]
        )

        logger.info(
            "[Reasoning] astrology: user=%s sign=%s period=%s interp=%d chars",
            user_id, sign, period, len(interpretation),
        )

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "astrology",
            "question": f"{zodiac['name_cn']} {period}运势",
            "cards": None,
            "interpretation": interpretation,
            "zodiac": zodiac,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._repo.create(record)
        self._persist_reading(user_id, record)
        return record

    # ── Dream ───────────────────────────────────────────────────

    def dream_interpretation(
        self, user_id: str, dream_description: str,
        emotion_before: Optional[str] = None,
    ) -> dict:
        memory_block = self._fetch_user_context(user_id, dream_description)
        mbti_block = self._fetch_mbti_block(user_id)

        user_msg = f"{memory_block}{mbti_block}我做了一个梦：{dream_description}"
        if emotion_before:
            user_msg += f"\n\n（我现在的情绪状态：{emotion_before}）"

        interpretation = self._llm.complete(
            DREAM_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}]
        )

        logger.info(
            "[Reasoning] dream interpretation: user=%s dream=%d chars interp=%d chars",
            user_id, len(dream_description), len(interpretation),
        )

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "dream",
            "question": dream_description,
            "cards": None,
            "interpretation": interpretation,
            "emotion_before": emotion_before,
            "emotion_after": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._repo.create(record)
        self._persist_reading(user_id, record)
        return record

    # ── Daily Fortune ───────────────────────────────────────────

    def daily_fortune(self, user_id: str, zodiac_sign: Optional[str] = None) -> dict:
        cards = draw_cards("single")
        card = cards[0]
        orientation = "逆位" if card["reversed"] else "正位"
        keyword = card["keyword_reversed"] if card["reversed"] else card["keyword_upright"]

        zodiac_part = ""
        if zodiac_sign and zodiac_sign in ZODIAC_BY_NAME:
            z = ZODIAC_BY_NAME[zodiac_sign]
            zodiac_part = f"用户的星座是{z['name_cn']}，星座特性：{z['keywords']}。"

        memory_block = self._fetch_user_context(user_id, "今日运势")
        mbti_block = self._fetch_mbti_block(user_id)

        user_msg = (
            f"{memory_block}{mbti_block}"
            f"请为用户抽取今日指引。{zodiac_part}"
            f"今日抽到的牌是：{card['name_cn']}（{card['name_en']}）{orientation}，"
            f"关键词：{keyword}。请基于这张牌给出今日运势指引。"
        )

        interpretation = self._llm.complete(
            DIVINATION_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}]
        )

        logger.info(
            "[Reasoning] daily fortune: user=%s card=%s(%s) interp=%d chars",
            user_id, card["name_cn"], orientation, len(interpretation),
        )

        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "fortune",
            "question": "今日运势",
            "cards": cards_to_json(cards),
            "interpretation": interpretation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._repo.create(record)
        self._persist_reading(user_id, record)
        return record

    # ── History & Stats ─────────────────────────────────────────

    def get_history(self, user_id: str, limit: int = 20) -> List[dict]:
        return self._repo.get_history(user_id, limit=limit)

    def get_stats(self, user_id: str) -> dict:
        return self._repo.get_stats(user_id)
