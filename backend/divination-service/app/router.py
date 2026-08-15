from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional

from .core.divination_service import DivinationService, DIVINATION_SYSTEM_PROMPT
from .core.llm_client import OpenAICompatibleLlmClient, AnthropicLlmClient, get_llm_client
from .core.community import (
    share_divination, list_public_shares, like_share, get_share, get_user_shares,
)
from .dto import (
    TarotRequestDto, AstrologyRequestDto, DreamRequestDto,
    DailyFortuneRequestDto, DivinationResponseDto,
)
import os

router = APIRouter(tags=["divination"])

_service = DivinationService()


def _build_service(api_key: Optional[str]) -> DivinationService:
    """Build a DivinationService with a custom LLM client from a header-provided key."""
    if not api_key:
        return _service
    api_key = api_key.strip()

    # Try OpenAI-compatible first (FIREAI, OpenRouter, etc.)
    base_url = (
        os.environ.get("LLM_BASE_URL", "").strip()
        or os.environ.get("OPENAI_BASE_URL", "").strip()
        or None
    )
    model = os.environ.get("LLM_MODEL", "glm-5.2")
    max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0.8"))
    top_p = float(os.environ.get("LLM_TOP_P", "0.9"))
    try:
        llm = OpenAICompatibleLlmClient(
            api_key=api_key, model=model,
            base_url=base_url, max_tokens=max_tokens,
            temperature=temperature, top_p=top_p,
        )
        return DivinationService(llm_client=llm)
    except ModuleNotFoundError:
        pass

    # Fallback: Anthropic-native
    try:
        llm = AnthropicLlmClient(
            api_key=api_key,
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "").strip() or None,
            max_tokens=int(os.environ.get("ANTHROPIC_MAX_TOKENS", "1024")),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.8")),
            top_p=float(os.environ.get("LLM_TOP_P", "0.9")),
        )
        return DivinationService(llm_client=llm)
    except ModuleNotFoundError:
        return _service


@router.post("/divination/tarot/draw", response_model=DivinationResponseDto)
def tarot_draw(
    dto: TarotRequestDto,
    x_api_key: Optional[str] = Header(default=None),
    x_anthropic_api_key: Optional[str] = Header(default=None),
):
    service = _build_service(x_api_key or x_anthropic_api_key)
    result = service.tarot_reading(
        user_id=dto.userId, question=dto.question,
        spread=dto.spread, emotion_before=dto.emotionBefore,
    )
    return DivinationResponseDto(**result)


# ==================== Real-LLM streaming + per-card readings ====================
#
# These endpoints always use the server-side configured LLM (8it.dev gateway,
# glm-5-turbo by default — see llm_client._DEFAULT_LLM_*). The API key is never
# exposed to the browser. Optional X-LLM-Base / X-LLM-Model headers allow a
# client to override the model/base for power users, but never the key.
#
# Public paths (no JWT required) so the showcase site can call them directly.

from pydantic import BaseModel as _PydTarot
from typing import List as _List

from .core.tarot_data import DECK as TAROT_DECK


class _StreamTarotDto(_PydTarot):
    userId: str = "_anon"
    question: str = ""
    spread: str = "three_card"
    emotionBefore: Optional[str] = None
    # When the client already drew cards visually, it can pass them here to get
    # an interpretation of THOSE exact cards instead of a server-side redraw.
    cards: Optional[_List[dict]] = None


def _resolve_llm_for_request(
    x_api_key: Optional[str],
    x_llm_base: Optional[str],
    x_llm_model: Optional[str],
):
    """Build an OpenAI-compatible client honouring optional base/model overrides.

    The key always comes from the request header (if provided) or the server
    environment / built-in default — never trusted from the browser otherwise.
    """
    api_key = (x_api_key or "").strip() or os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        api_key = None  # get_llm_client() will fall back to built-in default
    base_url = (x_llm_base or "").strip() or None
    model = (x_llm_model or "").strip() or None

    if api_key and (base_url or model):
        from .core.llm_client import _DEFAULT_LLM_API_KEY, _DEFAULT_LLM_BASE_URL, _DEFAULT_LLM_MODEL
        return OpenAICompatibleLlmClient(
            api_key=api_key,
            model=model or _DEFAULT_LLM_MODEL,
            base_url=base_url or _DEFAULT_LLM_BASE_URL,
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "1024")),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.8")),
            top_p=float(os.environ.get("LLM_TOP_P", "0.9")),
        )
    # No override → use the global client (built-in default applies).
    return _service._llm


def _build_user_message(question: str, cards_str: str, emotion_before: Optional[str], memory_block: str = "") -> str:
    msg = f"{memory_block}我的问题是：{question}\n\n我抽到的牌阵是：\n{cards_str}"
    if emotion_before:
        msg += f"\n\n（我现在的情绪状态：{emotion_before}）"
    return msg


@router.post("/divination/tarot/interpret-stream")
def tarot_interpret_stream(
    dto: _StreamTarotDto,
    x_api_key: Optional[str] = Header(default=None),
    x_llm_base: Optional[str] = Header(default=None),
    x_llm_model: Optional[str] = Header(default=None),
):
    """Stream a full tarot reading (SSE: text/event-stream of content deltas).

    Body: { userId, question, spread?, emotionBefore?, cards? }
    If `cards` is omitted the server draws fresh cards for the given spread.
    The first SSE event carries the drawn/used card list as JSON
    (`event: cards`), subsequent events are `event: delta` with text chunks,
    and a final `event: done` signals completion.
    """
    from .core.tarot_engine import draw_cards, format_cards_for_llm, cards_to_json

    llm = _resolve_llm_for_request(x_api_key, x_llm_base, x_llm_model)

    # Use client-provided cards if present, otherwise draw on the server.
    if dto.cards:
        # Enrich minimal cards ({name_en/name_cn, reversed, position}) with full
        # esoterica from the deck so the LLM gets rich context.
        cards = [_enrich_client_card(c) for c in dto.cards]
        cards_str = format_cards_for_llm(cards)
        cards_json = cards_to_json(cards)
    else:
        spread = dto.spread if dto.spread in ("single", "three_card", "celtic_cross", "relationship", "destiny_cross", "five_card") else "three_card"
        cards = draw_cards(spread)
        cards_str = format_cards_for_llm(cards)
        cards_json = cards_to_json(cards)

    memory_block = _service._fetch_user_context(dto.userId, dto.question or "tarot")
    user_msg = _build_user_message(dto.question or "请为我解读这个牌阵", cards_str, dto.emotionBefore, memory_block)
    messages = [{"role": "user", "content": user_msg}]

    import json

    def event_gen():
        try:
            yield _sse("cards", json.dumps(cards_json, ensure_ascii=False))
            full = []
            for delta in llm.stream_complete(DIVINATION_SYSTEM_PROMPT, messages):
                full.append(delta)
                yield _sse("delta", delta)
            yield _sse("done", "".join(full))
        except Exception as exc:
            yield _sse("error", f"{type(exc).__name__}: {exc}")

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable nginx buffering for true streaming
    })


def _sse(event: str, data: str) -> str:
    # SSE payload. `data` is sent verbatim; multi-line data is split across
    # consecutive `data:` lines per the SSE spec so EventSource reassembles it.
    escaped = data.replace("\n", "\ndata: ")
    return f"event: {event}\ndata: {escaped}\n\n"


def _format_minimal_cards(cards: list[dict]) -> str:
    """Format cards that only carry name/reversed/position (no full esoterica)."""
    lines = []
    for c in cards:
        name = c.get("name_cn") or c.get("name") or "?"
        orientation = "逆位" if c.get("reversed") else "正位"
        pos = c.get("position", "牌")
        lines.append(f"  [{pos}] {name} {orientation}")
    return "\n".join(lines)


def _enrich_client_card(c: dict) -> dict:
    """Merge a minimal client card ({name_en/name_cn, reversed, position}) with
    the full esoterica record from the 78-card deck. If the card can't be
    resolved, the minimal fields are kept so the LLM still gets something.
    """
    # Already a full deck record?
    if c.get("keyword_upright"):
        return c
    # Resolve by id first, then by name.
    card = None
    cid = c.get("id")
    if cid is not None and cid in TAROT_DECK:
        card = TAROT_DECK[cid]
    else:
        name_en = (c.get("name_en") or "").strip()
        name_cn = (c.get("name_cn") or "").strip()
        for entry in TAROT_DECK.values():
            if (name_en and name_en == entry["name_en"]) or (name_cn and name_cn == entry["name_cn"]):
                card = entry
                break
    if card is None:
        return c
    merged = card.copy()
    merged["reversed"] = bool(c.get("reversed", False))
    merged["position"] = c.get("position", "牌")
    return merged


class _CardReadingDto(_PydTarot):
    cardId: Optional[int] = None
    name: Optional[str] = None  # Chinese or English name fallback if id unknown
    reversed: bool = False
    question: str = ""
    userId: str = "_anon"


@router.post("/divination/tarot/card-reading")
def tarot_card_reading(
    dto: _CardReadingDto,
    x_api_key: Optional[str] = Header(default=None),
    x_llm_base: Optional[str] = Header(default=None),
    x_llm_model: Optional[str] = Header(default=None),
):
    """Non-streaming deep interpretation of a SINGLE card in the user's context.

    Looks the card up by id (or name) in the 78-card deck and asks the LLM for a
    focused 2-4 sentence reading that ties the card (upright or reversed) to the
    user's question. Used by the showcase's per-card 'AI 深度解读' button.
    """
    # Resolve card
    card = None
    if dto.cardId is not None and dto.cardId in TAROT_DECK:
        card = TAROT_DECK[dto.cardId]
    elif dto.name:
        needle = dto.name.strip().lower()
        for c in TAROT_DECK.values():
            if needle in (c["name_cn"], c["name_en"].lower()):
                card = c
                break
    if card is None:
        raise HTTPException(status_code=404, detail=f"card not found (id={dto.cardId}, name={dto.name})")

    orientation = "逆位" if dto.reversed else "正位"
    keyword = card["keyword_reversed"] if dto.reversed else card["keyword_upright"]
    desc = card["desc_reversed"] if dto.reversed else card["desc_upright"]

    from .core.tarot_esoterica import format_esoterica_for_prompt
    card_block = (
        f"[单牌深度解读] {card['name_cn']}（{card['name_en']}）{orientation}\n"
        f"关键词：{keyword}\n"
        f"牌意：{desc}\n"
        f"爱情指引：{card['love']}\n"
        f"事业指引：{card['career']}\n"
        f"健康指引：{card['health']}\n"
        f"神秘学对应：{format_esoterica_for_prompt(card['id'])}"
    )
    user_msg = (
        f"我的问题是：{dto.question or '请帮我深度解读这张牌'}\n\n"
        f"我抽到的牌：\n{card_block}"
    )

    llm = _resolve_llm_for_request(x_api_key, x_llm_base, x_llm_model)
    try:
        interpretation = llm.complete(DIVINATION_SYSTEM_PROMPT, [{"role": "user", "content": user_msg}])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")

    return {
        "card": {
            "id": card["id"],
            "name_cn": card["name_cn"],
            "name_en": card["name_en"],
            "suit": card.get("suit"),
            "reversed": dto.reversed,
            "orientation": orientation,
            "keyword": keyword,
            "description": desc,
        },
        "question": dto.question,
        "interpretation": interpretation,
        "model": getattr(llm, "_model", "unknown"),
    }


@router.post("/divination/astrology/horoscope", response_model=DivinationResponseDto)
def astrology_horoscope(
    dto: AstrologyRequestDto,
    x_api_key: Optional[str] = Header(default=None),
    x_anthropic_api_key: Optional[str] = Header(default=None),
):
    service = _build_service(x_api_key or x_anthropic_api_key)
    result = service.astrology_horoscope(
        user_id=dto.userId, zodiac_sign=dto.zodiacSign,
        birth_month=dto.birthMonth, birth_day=dto.birthDay,
        period=dto.period,
    )
    return DivinationResponseDto(**result)


@router.post("/divination/dream/interpret", response_model=DivinationResponseDto)
def dream_interpret(
    dto: DreamRequestDto,
    x_api_key: Optional[str] = Header(default=None),
    x_anthropic_api_key: Optional[str] = Header(default=None),
):
    service = _build_service(x_api_key or x_anthropic_api_key)
    result = service.dream_interpretation(
        user_id=dto.userId, dream_description=dto.dreamDescription,
        emotion_before=dto.emotionBefore,
    )
    return DivinationResponseDto(**result)


@router.post("/divination/daily-fortune", response_model=DivinationResponseDto)
def daily_fortune(
    dto: DailyFortuneRequestDto,
    x_api_key: Optional[str] = Header(default=None),
    x_anthropic_api_key: Optional[str] = Header(default=None),
):
    service = _build_service(x_api_key or x_anthropic_api_key)
    result = service.daily_fortune(user_id=dto.userId, zodiac_sign=dto.zodiacSign)
    return DivinationResponseDto(**result)


@router.get("/divination/history/{user_id}")
def get_history(user_id: str, limit: int = 20):
    return _service.get_history(user_id, limit=limit)


@router.get("/divination/stats/{user_id}")
def get_stats(user_id: str):
    return _service.get_stats(user_id)


# ==================== Community Sharing ====================

from pydantic import BaseModel as PydBaseModel

class ShareDto(PydBaseModel):
    userId: str
    nickname: str
    divinationId: str
    divType: str
    question: Optional[str] = None
    interpretation: str
    cards: Optional[list] = None

class LikeDto(PydBaseModel):
    userId: str


@router.post("/divination/share")
def share(dto: ShareDto):
    return share_divination(
        user_id=dto.userId, nickname=dto.nickname,
        divination_id=dto.divinationId, div_type=dto.divType,
        question=dto.question, interpretation=dto.interpretation,
        cards=dto.cards,
    )

@router.get("/divination/community")
def community_feed(limit: int = 50, offset: int = 0):
    return list_public_shares(limit=limit, offset=offset)

@router.post("/divination/community/{share_id}/like")
def community_like(share_id: str, dto: LikeDto):
    result = like_share(share_id, dto.userId)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="share not found")
    return result

@router.get("/divination/community/{share_id}")
def community_get(share_id: str):
    result = get_share(share_id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="share not found")
    return result

@router.get("/divination/community/user/{user_id}")
def community_user_shares(user_id: str):
    return get_user_shares(user_id)


# ==================== AI Proactive Recommendation ====================

import httpx as _httpx

_EMOTION_URL = os.environ.get("EMOTION_SERVICE_URL", "http://localhost:3009")

@router.get("/divination/recommend/{user_id}")
def recommend_divination(user_id: str):
    """
    AI proactive recommendation: analyze user's recent emotion trends and
    suggest the most appropriate divination form + personalized message.
    """
    try:
        resp = _httpx.get(f"{_EMOTION_URL}/emotion/recent/{user_id}", timeout=5.0)
        recent_emotion = resp.json() if resp.status_code == 200 else {}
    except Exception:
        recent_emotion = {}

    try:
        resp = _httpx.get(f"{_EMOTION_URL}/emotion/trends/{user_id}?days=7", timeout=5.0)
        trends = resp.json() if resp.status_code == 200 else {}
    except Exception:
        trends = {}

    emotion = recent_emotion.get("emotion", "calm") if recent_emotion else "calm"
    intensity = recent_emotion.get("intensity", 5) if recent_emotion else 5

    recommendations = {
        "anxiety": {
            "recommended": "fortune",
            "reason": "你最近似乎有些焦虑，抽取一张今日运势牌，给自己一个简单的指引和安心感。",
            "icon": "wb_sunny",
        },
        "sadness": {
            "recommended": "companion",
            "reason": "我感受到你有些低落，不需要占卜，让我陪你聊聊好吗？",
            "icon": "favorite",
        },
        "anger": {
            "recommended": "dream",
            "reason": "愤怒背后往往藏着深层情绪。试着回忆一下最近的梦境，让我帮你解读。",
            "icon": "bedtime",
        },
        "fear": {
            "recommended": "tarot",
            "reason": "面对未知的恐惧时，塔罗牌可以帮助你理清思绪，看到不同的视角。",
            "icon": "style",
        },
        "joy": {
            "recommended": "astrology",
            "reason": "你今天的状态很好！来看看星星本周还为你准备了什么惊喜。",
            "icon": "auto_awesome",
        },
        "calm": {
            "recommended": "tarot",
            "reason": "平静的心最适合占卜。你想问什么问题？让塔罗牌为你指引方向。",
            "icon": "style",
        },
        "surprise": {
            "recommended": "fortune",
            "reason": "生活给你带来了惊喜！抽一张牌看看这股能量会带你去哪里。",
            "icon": "wb_sunny",
        },
    }

    rec = recommendations.get(emotion, recommendations["calm"])

    stats = _service.get_stats(user_id)
    frequent_type = max(stats["by_type"], key=stats["by_type"].get) if stats["by_type"] else None

    return {
        "user_id": user_id,
        "current_emotion": emotion,
        "intensity": intensity,
        "recommended_divination": rec["recommended"],
        "reason": rec["reason"],
        "icon": rec["icon"],
        "most_used_divination": frequent_type,
        "total_divinations": stats["total_divinations"],
    }


# ==================== SFT Dataset Pipeline ====================

from pydantic import BaseModel as PydBaseModel2
from .core.sft_pipeline import TarotSFTGenerator, TarotEvaluator, generate_and_export

class SftGenerateDto(PydBaseModel2):
    n: int = 50
    mode: str = "template"  # "template" or "llm"


@router.post("/divination/sft/generate")
def sft_generate(dto: SftGenerateDto):
    """Generate a tarot SFT dataset and return stats + evaluation report."""
    return generate_and_export(n=dto.n, mode=dto.mode)


@router.get("/divination/sft/stats")
def sft_stats(n: int = 50, mode: str = "template"):
    """Preview dataset statistics without downloading."""
    return generate_and_export(n=n, mode=mode)


@router.get("/divination/sft/evaluate")
def sft_evaluate(n: int = 20):
    """Generate a small dataset and evaluate it against the 星语 persona rubric."""
    gen = TarotSFTGenerator()
    dataset = gen.generate_dataset(n=n, mode="template")
    evaluator = TarotEvaluator()
    return evaluator.evaluate(dataset)


# ==================== Tuya AI Agent Function-Call Endpoints ====================
#
# These read-only / write endpoints are designed to be called by the Tuya cloud
# AI Agent ("星语") via Function Call / MCP tools. They expose the 78-card
# esoterica data, emotion trends and task history so the agent can enrich its
# voice interpretation using real device-side draw results (uploaded via DP).
#
# See hardware/tuya-ai-your-chat-bot-copy/INTEGRATION.md §7.2 for the matching
# MCP tool config that consumes these endpoints.

from .core.tarot_data import DECK as TAROT_DECK, SUIT_LABELS_CN as TAROT_SUIT_CN


@router.get("/divination/tarot/cards")
def tarot_cards_list(suit: Optional[str] = None):
    """List all 78 cards (optionally filtered by suit).

    Used by the Agent to enumerate the deck or look up a card by name.
    """
    items = []
    for card in TAROT_DECK.values():
        if suit and card["suit"] != suit:
            continue
        items.append({
            "id": card["id"],
            "name_cn": card["name_cn"],
            "name_en": card["name_en"],
            "suit": card["suit"],
            "suit_cn": TAROT_SUIT_CN.get(card["suit"], card["suit"]),
            "keyword_upright": card["keyword_upright"],
            "keyword_reversed": card["keyword_reversed"],
        })
    return {"total": len(items), "cards": items}


@router.get("/divination/tarot/cards/{card_id}")
def tarot_card_detail(card_id: int, reversed: Optional[bool] = False):
    """Get full meaning of one card (id 0-77), including love/career/health.

    Query param `reversed=true` returns the reversed (逆位) interpretation;
    default is upright (正位).

    This is the endpoint referenced by the Agent's `get_tarot_card_meaning`
    Function Call tool — when the device DP uploads the drawn card, the agent
    looks up its full esoterica here to enrich the voice reading.
    """
    card = TAROT_DECK.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"card id {card_id} not found (0-77)")

    orientation = "reversed" if reversed else "upright"
    keyword = card["keyword_reversed"] if reversed else card["keyword_upright"]
    desc = card["desc_reversed"] if reversed else card["desc_upright"]

    return {
        "id": card["id"],
        "name_cn": card["name_cn"],
        "name_en": card["name_en"],
        "suit": card["suit"],
        "suit_cn": TAROT_SUIT_CN.get(card["suit"], card["suit"]),
        "orientation": orientation,
        "keyword": keyword,
        "description": desc,
        "love": card["love"],
        "career": card["career"],
        "health": card["health"],
    }


# Reuse the existing repository's create() for the history-save endpoint.
from pydantic import BaseModel as _PydBase2
from typing import Any as _Any


class HistorySaveDto(_PydBase2):
    userId: str
    divType: str                      # "tarot" | "astrology" | "dream" | "fortune"
    question: Optional[str] = None
    interpretation: Optional[str] = None
    cards: Optional[list] = None      # [{"id":0,"name":"愚者","rev":false,"pos":"过去"}]
    zodiacSign: Optional[str] = None
    emotionBefore: Optional[str] = None
    metadata: Optional[dict] = None   # arbitrary extra fields (e.g. device DP source)


@router.post("/divination/history")
def save_history(dto: HistorySaveDto):
    """Persist a divination record from the Agent (or device via gateway).

    Called by the Agent's `record_divination` Function Call tool after it has
    generated a voice interpretation, so the result shows up in the user's
    App history feed and emotion/task stats.
    """
    import time
    import uuid

    record = {
        "id": str(uuid.uuid4()),
        "user_id": dto.userId,
        "div_type": dto.divType,
        "question": dto.question,
        "interpretation": dto.interpretation,
        "cards": dto.cards,
        "zodiac_sign": dto.zodiacSign,
        "emotion_before": dto.emotionBefore,
        "created_at": int(time.time()),
        "source": "tuya_agent",
        **(dto.metadata or {}),
    }
    _service._repo.create(record)
    return {"ok": True, "id": record["id"], "saved": record}
