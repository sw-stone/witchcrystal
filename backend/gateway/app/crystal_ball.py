"""
水晶球状态同步模块 —— ESP32 ↔ 网关 ↔ 手机 web 端。

ESP32 状态变化时 POST /device/state → 网关缓存 + 广播到 web WS /ws/crystal。
手机 web 端按钮反过来 POST /device/command → 网关下发到 ESP32（设备通道待接，先缓存/占位）。

状态 JSON（ESP32 上报 / web 接收）：
  {"device_id":"crystal_ball_01","mode":"divination","listening":true,
   "led":"purple","ai_thinking":false,"ts":1700000000}

命令 JSON（web 发送 → 网关 → ESP32，待设备通道接通）：
  {"cmd":"set_mode","mode":"whitenoise"} | {"cmd":"start_voice"} | {"cmd":"stop_voice"}
"""
import asyncio
import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["crystal-ball"])

# 当前水晶球状态（内存缓存，ESP32 上报时更新）
_current_state: dict = {
    "device_id": "crystal_ball_01",
    "mode": "standby",
    "listening": False,
    "led": "white",
    "ai_thinking": False,
    "ts": 0,
}

# 已连接的 web 客户端（手机/浏览器）
_web_clients: set[WebSocket] = set()
# 待下发给 ESP32 的命令队列（ESP32 轮询 GET /device/command/pending 拉取）
_pending_commands: list[dict] = []


class StateReport(BaseModel):
    device_id: str = "crystal_ball_01"
    mode: str = "standby"
    listening: bool = False
    led: str = "white"
    ai_thinking: bool = False


class DeviceCommand(BaseModel):
    cmd: str
    mode: Optional[str] = None
    spread: Optional[str] = None
    hour: Optional[int] = None
    minute: Optional[int] = None


async def _broadcast_state(state: dict) -> None:
    """把状态广播给所有 web 客户端"""
    dead = []
    for ws in _web_clients:
        try:
            await ws.send_text(json.dumps(state, ensure_ascii=False))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _web_clients.discard(ws)


@router.post("/device/state")
async def device_state(state: StateReport):
    """ESP32 上报当前状态 → 网关缓存 + 广播到 web"""
    global _current_state
    _current_state = state.dict()
    _current_state["ts"] = int(time.time())
    await _broadcast_state(_current_state)
    return {"ok": True}


@router.get("/device/state")
async def get_state():
    """web/调试查询当前状态"""
    return _current_state


@router.post("/device/command")
async def device_command(cmd: DeviceCommand):
    """web 端下发命令 → 网关缓存，等 ESP32 轮询拉取。
    命令格式：{cmd, mode?, spread?, hour?, minute?}"""
    payload = cmd.dict(exclude_none=True)
    payload["ts"] = int(time.time())
    _pending_commands.append(payload)
    logger.info("[Crystal] command queued: %s", payload)
    return {"ok": True, "queued": len(_pending_commands)}


@router.get("/device/command/pending")
async def get_pending_commands():
    """ESP32 轮询拉取待执行命令。拉取即清空队列。"""
    cmds = list(_pending_commands)
    _pending_commands.clear()
    return {"commands": cmds}


@router.websocket("/ws/crystal")
async def ws_crystal(ws: WebSocket):
    """web 端连接此 WS 实时接收水晶球状态。
    连上时先推一次当前状态。"""
    await ws.accept()
    _web_clients.add(ws)
    logger.info("[Crystal] web client connected, total=%d", len(_web_clients))
    try:
        await ws.send_text(json.dumps(_current_state, ensure_ascii=False))
        # 保持连接，仅接收（web 端若要发命令走 HTTP POST /device/command）
        while True:
            await ws.receive_text()  # 忽略 web→server 文本，命令走 HTTP
    except WebSocketDisconnect:
        pass
    finally:
        _web_clients.discard(ws)
        logger.info("[Crystal] web client disconnected, total=%d", len(_web_clients))
