"""
语音对话端点 —— ASR + TTS + LLM 流式，供手机 web 端实时语音交互。

端点：
  POST /voice/asr     音频 blob(多部分) → 识别文本
                       走 active asr provider（Whisper 兼容 /audio/transcriptions）
  POST /voice/tts     {text} → MP3 音频流（chunked transfer，边生成边传）
                       走 active tts provider（ElevenLabs /v1/text-to-speech/{voice}）
  POST /voice/chat    SSE：ASR 内联 + LLM 流式 + TTS 不在此端点（web 拿 delta 后自己请求 TTS）
                       实际 web 端 pipeline：mic→/voice/asr→/llm/chat(SSE)→/voice/tts
  GET  /voice/active?type=asr|tts   查当前启用的 asr/tts provider（web 端拉配置用）

流式 + 打断：
  - web 端 VAD 检测用户说话 → 中止正在播的 TTS audio → 启动新一轮 ASR
  - LLM SSE 逐字下发，web 边收边喂 TTS（按句切分）
  - 用户打断时 web abort 当前 fetch + 停 audio
"""
import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse

from app.llm_config import get_active_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/active")
async def voice_active(type: str = "tts"):
    """查 asr/tts provider 配置（含完整 api_key，供 web 端直连或后端代理用）。"""
    if type not in ("asr", "tts"):
        raise HTTPException(status_code=400, detail="type must be asr or tts")
    p = get_active_provider(type)
    if not p:
        return JSONResponse(status_code=404, content={"detail": f"no active {type} provider"})
    return {
        "id": p["id"], "name": p["name"],
        "base_url": p["base_url"], "api_key": p["api_key"],
        "model": p["model"], "type": p.get("type", type),
        "extra": p.get("extra", {}),
    }


@router.post("/asr")
async def voice_asr(audio: UploadFile = File(...)):
    """语音转文字。接收音频文件（web 端用 MediaRecorder 录制 webm/opus），
    转发到 active asr provider（Whisper 兼容 /audio/transcriptions）。
    返回 {"text": "..."}"""
    p = get_active_provider("asr")
    if not p:
        raise HTTPException(status_code=400, detail="no active asr provider configured")
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="empty audio")

    url = p["base_url"].rstrip("/") + "/audio/transcriptions"
    files = {
        "file": (audio.filename or "audio.webm", audio_bytes, audio.content_type or "audio/webm"),
    }
    data = {"model": p["model"] or "whisper-1", "response_format": "json"}
    headers = {"Authorization": f"Bearer {p['api_key']}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, files=files, data=data, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"asr upstream unreachable: {exc}")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])
    try:
        result = resp.json()
    except Exception:
        result = {"text": resp.text}
    return {"text": result.get("text", ""), "raw": result}


@router.post("/tts")
async def voice_tts(request: Request):
    """文字转语音，流式返回 MP3。
    请求体：{text, voice?, speed?, stability?, similarity_boost?}
    走 active tts provider（ElevenLabs /v1/text-to-speech/{voice}）。
    返回 audio/mpeg 流，web 端用 <audio> 或 AudioContext 播放。"""
    p = get_active_provider("tts")
    if not p:
        raise HTTPException(status_code=400, detail="no active tts provider configured")
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    voice = body.get("voice") or p["model"] or "default"
    tts_path_tpl = p.get("extra", {}).get("tts_path", "/v1/text-to-speech/{voice}")
    tts_path = tts_path_tpl.replace("{voice}", voice)
    url = p["base_url"].rstrip("/") + tts_path

    payload = {
        "text": text,
        "model_id": p.get("extra", {}).get("model_id", "eleven_multilingual_v2"),
        "voice_settings": {
            "stability": body.get("stability", 0.5),
            "similarity_boost": body.get("similarity_boost", 0.75),
            "speed": body.get("speed", 1.0),
        },
    }
    headers = {
        "xi-api-key": p["api_key"],
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    async def stream_audio():
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as upstream:
                async for chunk in upstream.aiter_raw():
                    yield chunk

    return StreamingResponse(stream_audio(), media_type="audio/mpeg")


@router.post("/chat-stream")
async def voice_chat_stream(request: Request):
    """LLM 流式对话（SSE）。请求体原样转发到 active llm provider 的
    /chat/completions（带 stream:true），逐 token 下发给 web 端。
    web 端拿到 delta 后按句切分请求 /voice/tts。

    请求体：{messages:[...], model?, tools?, ...}（OpenAI 兼容）
    响应：SSE，data: {delta} 逐字"""
    p = get_active_provider("llm")
    if not p:
        raise HTTPException(status_code=400, detail="no active llm provider configured")
    try:
        body = await request.json()
    except Exception:
        body = {}
    body["stream"] = True  # 强制流式
    if "model" not in body or body["model"] == "auto":
        body["model"] = p["model"]

    url = p["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {p['api_key']}",
    }

    async def sse_stream():
        timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=body, headers=headers) as upstream:
                async for line in upstream.aiter_lines():
                    if not line:
                        continue
                    # OpenAI SSE 格式：data: {...}\n\n
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            obj = json.loads(data)
                            delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
                        except Exception:
                            continue

    return StreamingResponse(sse_stream(), media_type="text/event-stream")
