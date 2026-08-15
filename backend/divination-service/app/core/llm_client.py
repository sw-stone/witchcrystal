"""
LLM client for divination interpretations.
Supports OpenAI-compatible APIs (primary) and Anthropic-native APIs (fallback).
Auto-detects provider based on environment configuration.
"""
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TypedDict
import logging

logger = logging.getLogger(__name__)


class ChatMessage(TypedDict):
    role: str
    content: str


class LlmClient(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, messages: List[ChatMessage]) -> str:
        ...

    def stream_complete(self, system_prompt: str, messages: List[ChatMessage]):
        """Default streaming: run complete() and yield the whole result once."""
        yield self.complete(system_prompt, messages)


def _load_local_env() -> None:
    for path in [Path.cwd() / ".env.local"]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# 在模块导入时加载一次 .env.local，避免每次调用 get_llm_client() 都重新注入，
# 否则测试里 monkeypatch.delenv() 后会被 get_llm_client() 内部的 _load_local_env()
# 再次 setdefault 回来，导致 Mock 降级分支永远走不到。
_load_local_env()


class OpenAICompatibleLlmClient(LlmClient):
    """Works with any OpenAI-compatible endpoint (OpenAI, FIREAI, OpenRouter, etc.)"""

    def __init__(self, api_key: str, model: str = "glm-5.2",
                 base_url: Optional[str] = None, max_tokens: int = 1024,
                 temperature: float = 0.8, top_p: float = 0.9) -> None:
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url.rstrip("/")
        self._client = OpenAI(**kwargs)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p

    def complete(self, system_prompt: str, messages: List[ChatMessage]) -> str:
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages += [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            messages=full_messages,
        )
        return resp.choices[0].message.content or ""

    def stream_complete(self, system_prompt: str, messages: List[ChatMessage]):
        """Yield content deltas (str) as they arrive from the model.

        Falls back to the non-streaming complete() if the SDK does not support
        streaming for any reason, yielding the full text as a single chunk.
        """
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages += [{"role": m["role"], "content": m["content"]} for m in messages]
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
                messages=full_messages,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as exc:
            logger.warning("LLM stream failed (%s); falling back to non-stream", exc)
            yield self.complete(system_prompt, messages)


class AnthropicLlmClient(LlmClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6",
                 base_url: Optional[str] = None, max_tokens: int = 1024,
                 temperature: float = 0.8, top_p: float = 0.9) -> None:
        import anthropic
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url.rstrip("/")
        self._client = anthropic.Anthropic(**kwargs)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p

    def complete(self, system_prompt: str, messages: List[ChatMessage]) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            system=system_prompt,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


import re


class MockLlmClient(LlmClient):
    def complete(self, system_prompt: str, messages: List[ChatMessage]) -> str:
        last_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

        cards = self._extract_cards(last_msg)
        if cards:
            return self._card_aware_mock(last_msg, cards)

        return (
            f"（占位解读）我感应到了你关于「{last_msg[:40]}」的疑问。"
            "星象告诉我，这是一个充满可能性的时刻。"
            "牌面显示着转变与希望的交织——保持开放的心态，"
            "命运的齿轮正在为你转动。记住，每一次抽牌都是与内心的对话。"
            "（当前使用占位LLM，未配置真实API Key）"
        )

    @staticmethod
    def _extract_cards(msg: str) -> list[dict]:
        cards = []
        pattern = re.compile(
            r'\[([^\]]+)\]\s*([^\n（]+)（[^）]*）(正位|逆位)\s*\n\s*关键词：(.+?)(?:\n\s*牌意：(.+?))?(?:\n|$)',
            re.DOTALL,
        )
        for m in pattern.finditer(msg):
            cards.append({
                "position": m.group(1).strip(),
                "name_cn": m.group(2).strip(),
                "orientation": m.group(3),
                "keyword": m.group(4).strip(),
                "desc": (m.group(5) or "").strip(),
            })
        return cards

    @staticmethod
    def _card_aware_mock(question_msg: str, cards: list[dict]) -> str:
        q_match = re.search(r'我的问题是[：:]\s*(.+)', question_msg)
        question = q_match.group(1).strip()[:60] if q_match else "你的问题"

        parts = [f"星语感应到了你关于「{question}」的心声……\n"]
        for c in cards:
            kw = c["keyword"]
            desc = c["desc"]
            if desc:
                snippet = desc[:50]
                parts.append(
                    f"〔{c['position']}〕{c['name_cn']} {c['orientation']}——"
                    f"{kw}。{snippet}……"
                )
            else:
                parts.append(
                    f"〔{c['position']}〕{c['name_cn']} {c['orientation']}——{kw}。"
                )
        first_card = cards[0]
        parts.append(
            f"\n综合牌阵来看，星辰指引你关注「{first_card['keyword'].split()[0]}」的力量。"
            "记住，塔罗是一面镜子，映照的是你内心已经知晓的答案。"
            "（当前使用占位LLM，未配置真实API Key）"
        )
        return "\n".join(parts)


# Built-in default LLM configuration (used when no LLM_* env vars are set).
# These ship with the code so the deployed container works out of the box.
# Override at runtime with LLM_API_KEY / LLM_BASE_URL / LLM_MODEL env vars.
_DEFAULT_LLM_API_KEY = "sk-FYGi7nOVVCkdDckq4fc6zAjKDfRhye6gqhbLYzFUzATajFno"
_DEFAULT_LLM_BASE_URL = "https://api.8it.dev/v1"
_DEFAULT_LLM_MODEL = "glm-5-turbo"


def get_llm_client() -> LlmClient:
    # Optional per-request override from gateway (X-LLM-Base / X-LLM-Model headers)
    req_base = os.environ.get("_REQ_LLM_BASE_URL", "").strip()
    req_model = os.environ.get("_REQ_LLM_MODEL", "").strip()

    # Priority 1: OpenAI-compatible (FIREAI, OpenRouter, native OpenAI, etc.)
    # Key resolution: request header key → env → built-in default.
    llm_api_key = (
        os.environ.get("LLM_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("FIREAI_API_KEY", "").strip()
        or _DEFAULT_LLM_API_KEY
    )
    if llm_api_key:
        model = (
            req_model
            or os.environ.get("LLM_MODEL", "").strip()
            or _DEFAULT_LLM_MODEL
        )
        base_url = (
            req_base
            or os.environ.get("LLM_BASE_URL", "").strip()
            or os.environ.get("OPENAI_BASE_URL", "").strip()
            or _DEFAULT_LLM_BASE_URL
        )
        max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0.8"))
        top_p = float(os.environ.get("LLM_TOP_P", "0.9"))
        try:
            client = OpenAICompatibleLlmClient(
                api_key=llm_api_key, model=model,
                base_url=base_url, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p,
            )
            logger.info("LLM client: OpenAI-compatible (model=%s, base_url=%s)", model, base_url or "default")
            return client
        except ModuleNotFoundError as exc:
            if exc.name != "openai":
                raise
            logger.warning("openai package not installed, falling back")

    # Priority 2: Anthropic-native
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip() or None
        max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "1024"))
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0.8"))
        top_p = float(os.environ.get("LLM_TOP_P", "0.9"))
        try:
            client = AnthropicLlmClient(
                api_key=anthropic_key, model=model,
                base_url=base_url, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p,
            )
            logger.info("LLM client: Anthropic-native (model=%s)", model)
            return client
        except ModuleNotFoundError as exc:
            if exc.name != "anthropic":
                raise
            logger.warning("anthropic package not installed, falling back to mock")

    logger.info("LLM client: Mock (no API key configured)")
    return MockLlmClient()
