"""
LLM/TTS/Voice Provider 配置管理 —— 支持运行时添加/修改/选择多个 AI 服务。

Provider 类型（type 字段）：
  - "llm"   : 文本对话 LLM（OpenAI 兼容 /chat/completions），如 magikcloud GLM-5.2
  - "tts"   : 文字转语音 TTS，如 ElevenLabs（预留，ESP32 端调用接口待接）
  - "voice" : 端到端语音对话，如 Moshi（全双工 WebSocket，天然支持 barge-in）

每种 type 独立维护"当前启用"，互不影响：
  - LLM 用于文本占卜解读（非语音路径）
  - Voice 用于实时语音对话（主对话链路）
  - TTS 作为可选的高品质单边语音输出（后续可替换 Moshi 的 TTS 段）

数据持久化到 gateway/llm_providers.json。
向后兼容：无 type 字段的旧记录视为 "llm"。

接口：
  GET    /llm/providers?type=xxx       列出（api_key 脱敏）
  POST   /llm/providers                新增（带 type）
  PUT    /llm/providers/{id}           修改
  DELETE /llm/providers/{id}           删除
  POST   /llm/providers/{id}/activate  设为该 type 的启用项
  GET    /llm/active?type=xxx          取该 type 启用项（含完整 api_key，供设备端）
  POST   /llm/chat                     代理转发到 active llm provider
  POST   /llm/tts                      代理转发到 active tts provider（预留）
"""
import json
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/llm", tags=["llm"])

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "llm_providers.json"

VALID_TYPES = {"llm", "tts", "voice", "asr"}


class ProviderIn(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    type: str = "llm"          # llm | tts | voice
    active: bool = False
    extra: dict = {}           # 预留：ws_path / voice_format / sample_rate 等


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None
    active: Optional[bool] = None
    extra: Optional[dict] = None


def _load() -> dict:
    if not _CONFIG_PATH.exists():
        return {"providers": []}
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"providers": []}
    # 向后兼容：旧记录无 type 视为 llm
    for p in data.get("providers", []):
        p.setdefault("type", "llm")
        p.setdefault("extra", {})
    return data


def _save(data: dict) -> None:
    _CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


def _to_public(p: dict) -> dict:
    return {
        "id": p["id"],
        "name": p["name"],
        "base_url": p["base_url"],
        "api_key": _mask_key(p.get("api_key", "")),
        "model": p["model"],
        "type": p.get("type", "llm"),
        "active": p.get("active", False),
        "extra": p.get("extra", {}),
    }


def _find(data: dict, pid: str) -> Optional[dict]:
    for p in data["providers"]:
        if p["id"] == pid:
            return p
    return None


def get_active_provider(ptype: str = "llm") -> Optional[dict]:
    """取指定 type 的启用 provider（含完整 api_key）。供设备端/代理转发用。"""
    if ptype not in VALID_TYPES:
        return None
    data = _load()
    for p in data["providers"]:
        if p.get("type", "llm") == ptype and p.get("active"):
            return p
    return None


@router.get("/providers")
async def list_providers(type: Optional[str] = None):
    data = _load()
    items = data["providers"]
    if type:
        if type not in VALID_TYPES:
            raise HTTPException(status_code=400, detail=f"invalid type, must be one of {VALID_TYPES}")
        items = [p for p in items if p.get("type", "llm") == type]
    return {"providers": [_to_public(p) for p in items]}


@router.post("/providers")
async def add_provider(body: ProviderIn):
    if body.type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid type, must be one of {VALID_TYPES}")
    data = _load()
    pid = body.name.lower().replace(" ", "_")[:24] or body.type + "_" + str(len(data["providers"]))
    if _find(data, pid):
        pid += "_" + str(len(data["providers"]))
    if body.active:
        for p in data["providers"]:
            if p.get("type", "llm") == body.type:
                p["active"] = False
    new = {
        "id": pid,
        "name": body.name,
        "base_url": body.base_url,
        "api_key": body.api_key,
        "model": body.model,
        "type": body.type,
        "active": body.active,
        "extra": body.extra,
    }
    data["providers"].append(new)
    _save(data)
    return _to_public(new)


@router.put("/providers/{pid}")
async def update_provider(pid: str, body: ProviderUpdate):
    data = _load()
    p = _find(data, pid)
    if not p:
        raise HTTPException(status_code=404, detail="provider not found")
    if body.name is not None:
        p["name"] = body.name
    if body.base_url is not None:
        p["base_url"] = body.base_url
    if body.api_key is not None:
        p["api_key"] = body.api_key
    if body.model is not None:
        p["model"] = body.model
    if body.type is not None:
        if body.type not in VALID_TYPES:
            raise HTTPException(status_code=400, detail=f"invalid type")
        p["type"] = body.type
    if body.extra is not None:
        p["extra"] = body.extra
    if body.active is True:
        ptype = p.get("type", "llm")
        for other in data["providers"]:
            if other.get("type", "llm") == ptype:
                other["active"] = (other is p)
    _save(data)
    return _to_public(p)


@router.delete("/providers/{pid}")
async def delete_provider(pid: str):
    data = _load()
    before = len(data["providers"])
    data["providers"] = [p for p in data["providers"] if p["id"] != pid]
    if len(data["providers"]) == before:
        raise HTTPException(status_code=404, detail="provider not found")
    _save(data)
    return {"ok": True}


@router.post("/providers/{pid}/activate")
async def activate_provider(pid: str):
    data = _load()
    p = _find(data, pid)
    if not p:
        raise HTTPException(status_code=404, detail="provider not found")
    ptype = p.get("type", "llm")
    for other in data["providers"]:
        if other.get("type", "llm") == ptype:
            other["active"] = (other is p)
    _save(data)
    return _to_public(p)


@router.get("/active")
async def get_active(request: Request):
    """返回指定 type 的启用 provider（含完整 api_key）。
    默认 type=llm。设备端拉 voice/tts 配置时传 ?type=voice / ?type=tts。"""
    ptype = request.query_params.get("type", "llm")
    if ptype not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid type")
    p = get_active_provider(ptype)
    if not p:
        return JSONResponse(status_code=404, content={"detail": f"no active {ptype} provider"})
    return {
        "id": p["id"],
        "name": p["name"],
        "base_url": p["base_url"],
        "api_key": p["api_key"],
        "model": p["model"],
        "type": p.get("type", "llm"),
        "extra": p.get("extra", {}),
    }


@router.post("/chat")
async def proxy_chat(request: Request):
    """代理转发到 active llm provider 的 /chat/completions（OpenAI 兼容）。"""
    p = get_active_provider("llm")
    if not p:
        raise HTTPException(status_code=400, detail="no active llm provider configured")
    try:
        body = await request.body()
    except Exception:
        body = b""
    url = p["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {p['api_key']}",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, content=body, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"upstream unreachable: {exc}")
    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
        headers={"X-LLM-Provider": p["id"]},
    )


@router.post("/tts")
async def proxy_tts(request: Request):
    """代理转发到 active tts provider（ElevenLabs 等）。预留接口。
    请求体原样转发，路径按 provider.extra.tts_path（默认 /v1/text-to-speech/{model}）。"""
    p = get_active_provider("tts")
    if not p:
        raise HTTPException(status_code=400, detail="no active tts provider configured")
    try:
        body = await request.body()
    except Exception:
        body = b""
    tts_path = p.get("extra", {}).get("tts_path", "/v1/text-to-speech/" + p["model"])
    url = p["base_url"].rstrip("/") + tts_path
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": p["api_key"],          # ElevenLabs 用 xi-api-key
        "Authorization": f"Bearer {p['api_key']}",  # 兼容其它 TTS
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, content=body, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"upstream unreachable: {exc}")
    return JSONResponse(
        status_code=resp.status_code,
        content={"ok": resp.ok, "bytes": len(resp.content)},
        headers={"X-TTS-Provider": p["id"]},
    )
