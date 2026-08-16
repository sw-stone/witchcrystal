"""
水晶球状态同步模块 —— ESP32 ↔ 网关 ↔ 手机 web 端（屿眠 Sleep Isle v2）。

== 产品链路状态机（对应《软件与硬件交互逻辑说明》）==

状态（sleep_flow.state）：
  black_standby  黑屏待机（初始；停一切软件内容，仅监听硬件信号）
  onboarding     播放 引入.mp4（首次使用引导）
  locked         播放 锁定.mp4（手机已锁定·睡眠魔法激活中）→ 播完进 ai_standby
  ai_standby     AI 待机：循环播放 AI待机.mp4
  ai_speaking    AI 正在说话：播放 AI说话.mp4（与 ai_standby 互斥）
  module         助眠模块 HTML（冥想/白噪音/呼吸/塔罗），AI 语音时叠加说话动态规则
  tarot_cast     塔罗转场.mp4 → 卡牌上浮动画 → AI 解读（顺序执行）
  alarm          闹钟：闹钟.mp4 + 闹钟音频，等待停止信号
  celebrating    欢呼.mp4 → 播完回 ai_standby

硬件信号（POST /device/signal {"event": "..."}）：
  joy_front   遥感按钮-前 → 任意状态 → onboarding（引入.mp4）
  joy_back    遥感按钮-后 → 任意状态 → black_standby（强制，优先级最高）
  joy_down    遥感按钮-下 → black_standby/onboarding → locked（手机放入底座）
              闹钟响时（alarm）→ 停止闹钟 → celebrating
  alarm_stop  停止闹钟按键信号（与 joy_down 在闹钟态等效）

web/软件侧信号（POST /app/signal）：
  enter_module {"module":"meditation|whitenoise|breathing|tarot"} → module
  ai_voice     {"speaking":true|false} → ai_speaking / 回原状态
  tarot_voice_draw → tarot_cast 序列
  alarm_fire   → alarm（到达预设闹钟时间）

ESP32 兼容旧接口：POST /device/state（模式上报）仍保留。
广播：WS /ws/crystal 推送完整 sleep_flow 状态（含 video/screen 指令）。
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

# ---------------------------------------------------------------------------
# 视频清单（文件名与《交互逻辑说明》严格一致，勿改名）
# ---------------------------------------------------------------------------
VIDEO = {
    "onboarding":  "/static/video/引入.mp4",
    "locked":      "/static/video/锁定.mp4",
    "ai_standby":  "/static/video/AI待机.mp4",
    "ai_speaking": "/static/video/AI说话.mp4",
    "tarot_cast":  "/static/video/塔罗转场.mp4",
    "alarm":       "/static/video/闹钟.mp4",
    "celebrate":   "/static/video/欢呼.mp4",
}

MODULES = {
    "meditation":  {"title": "睡前冥想", "url": "/static/meditation/meditation.html"},
    "whitenoise":  {"title": "声光场景", "url": "/static/whitenoise/whitenoise.html"},
    "breathing":   {"title": "呼吸引导", "url": "/static/breathing/breathing-orbit.html"},
    "tarot":       {"title": "塔罗占卜", "url": "/static/tarot.html"},
}

# ---------------------------------------------------------------------------
# 链路状态机
# ---------------------------------------------------------------------------
_sleep_flow: dict = {
    "state": "black_standby",     # 见模块 docstring
    "prev_state": None,           # ai_speaking 结束后返回的目标
    "video": None,                # 当前应播放视频 URL（None=黑屏）
    "video_loop": False,          # AI待机 循环
    "module": None,               # module 态下的模块 key
    "alarm_audio": False,         # alarm 态：闹钟音频开关
    "seq": 0,                     # 递增序号，web 端去重
    "ts": 0,
}

# 兼容旧模式状态（ESP32 v1 固件 / 测试 tab）
_current_state: dict = {
    "device_id": "crystal_ball_01",
    "mode": "standby",
    "listening": False,
    "led": "white",
    "ai_thinking": False,
    "ts": 0,
}

_web_clients: set[WebSocket] = set()
_pending_commands: list[dict] = []


def _set_flow(state: str, **kw) -> dict:
    """切换链路状态并生成展示指令。"""
    _sleep_flow["prev_state"] = _sleep_flow["state"] if state == "ai_speaking" else _sleep_flow.get("prev_state")
    _sleep_flow["state"] = state
    _sleep_flow["seq"] += 1
    _sleep_flow["ts"] = int(time.time())

    # 各态默认展示
    defaults = {
        "black_standby": {"video": None, "video_loop": False, "module": None, "alarm_audio": False},
        "onboarding":    {"video": VIDEO["onboarding"], "video_loop": False, "module": None, "alarm_audio": False},
        "locked":        {"video": VIDEO["locked"], "video_loop": False, "module": None, "alarm_audio": False},
        "ai_standby":    {"video": VIDEO["ai_standby"], "video_loop": True, "module": None, "alarm_audio": False},
        "ai_speaking":   {"video": VIDEO["ai_speaking"], "video_loop": False, "alarm_audio": False},
        "module":        {"video": None, "alarm_audio": False},   # module 页内自行渲染；AI 语音时叠加 ai_speaking
        "tarot_cast":    {"video": VIDEO["tarot_cast"], "video_loop": False, "alarm_audio": False},
        "alarm":         {"video": VIDEO["alarm"], "video_loop": True, "module": None, "alarm_audio": True},
        "celebrating":   {"video": VIDEO["celebrate"], "video_loop": False, "module": None, "alarm_audio": False},
    }
    for k, v in defaults.get(state, {}).items():
        _sleep_flow[k] = v
    _sleep_flow.update(kw)
    return _sleep_flow


async def _broadcast(payload: dict) -> None:
    dead = []
    for ws in _web_clients:
        try:
            await ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _web_clients.discard(ws)


async def _broadcast_flow() -> None:
    await _broadcast({"type": "sleep_flow", **_sleep_flow})


class SignalReport(BaseModel):
    device_id: str = "crystal_ball_01"
    event: str  # joy_front | joy_back | joy_down | alarm_stop


class AppSignal(BaseModel):
    event: str                    # enter_module | ai_voice | tarot_voice_draw | alarm_fire | module_exit
    module: Optional[str] = None  # meditation|whitenoise|breathing|tarot
    speaking: Optional[bool] = None


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


@router.post("/device/signal")
async def device_signal(sig: SignalReport):
    """ESP32 v2 硬件信号 → 链路状态机。"""
    ev = sig.event
    st = _sleep_flow["state"]

    if ev == "joy_back":
        # 遥感按钮-后：强制返回黑屏待机（优先级最高）
        _set_flow("black_standby")

    elif ev == "joy_front":
        # 遥感按钮-前：首次使用引导（按信号触发，不做一次性判断）
        _set_flow("onboarding")

    elif ev in ("joy_down", "alarm_stop"):
        if st == "alarm":
            # 停止闹钟按键信号 → 起床庆祝（先停音频/视频，由状态切换表达）
            _set_flow("celebrating")
        elif st in ("black_standby", "onboarding"):
            # 遥感按钮-下：手机放入底座 → 锁定视频
            _set_flow("locked")
        else:
            # 其他状态按下：不改变链路（信号按场景消费）
            return {"ok": True, "consumed": False, "state": st}

    await _broadcast_flow()
    logger.info("[SleepIsle] hw signal %s: %s -> %s", ev, st, _sleep_flow["state"])
    return {"ok": True, **_sleep_flow}


@router.post("/app/signal")
async def app_signal(sig: AppSignal):
    """软件/页面侧信号 → 链路状态机。"""
    st = _sleep_flow["state"]

    if sig.event == "enter_module" and sig.module in MODULES:
        _set_flow("module", module=sig.module)

    elif sig.event == "module_exit":
        _set_flow("ai_standby")

    elif sig.event == "ai_voice":
        if sig.speaking:
            if st == "ai_speaking":
                return {"ok": True, "state": st}
            _set_flow("ai_speaking", prev_state=st if st != "ai_speaking" else _sleep_flow.get("prev_state"))
        else:
            back = _sleep_flow.get("prev_state") or "ai_standby"
            if back == "ai_speaking":
                back = "ai_standby"
            _set_flow(back)

    elif sig.event == "tarot_voice_draw":
        # 塔罗语音抽卡：转场视频 → 卡牌动画（页面负责）→ AI 解读（页面经 ai_voice 驱动）
        _set_flow("tarot_cast", module="tarot")

    elif sig.event == "alarm_fire":
        _set_flow("alarm")

    await _broadcast_flow()
    logger.info("[SleepIsle] app signal %s: %s -> %s", sig.event, st, _sleep_flow["state"])
    return {"ok": True, **_sleep_flow}


@router.get("/sleep-flow")
async def get_flow():
    """查询当前链路状态（页面加载时对齐）。"""
    return _sleep_flow


# ---------------------------------------------------------------------------
# 兼容 v1：模式上报 / 命令队列
# ---------------------------------------------------------------------------

@router.post("/device/state")
async def device_state(state: StateReport):
    global _current_state
    _current_state = state.dict()
    _current_state["ts"] = int(time.time())
    await _broadcast(_current_state)
    return {"ok": True}


@router.get("/device/state")
async def get_state():
    return _current_state


@router.post("/device/command")
async def device_command(cmd: DeviceCommand):
    payload = cmd.dict(exclude_none=True)
    payload["ts"] = int(time.time())
    _pending_commands.append(payload)
    logger.info("[Crystal] command queued: %s", payload)
    return {"ok": True, "queued": len(_pending_commands)}


@router.get("/device/command/pending")
async def get_pending_commands():
    cmds = list(_pending_commands)
    _pending_commands.clear()
    return {"commands": cmds}


@router.websocket("/ws/crystal")
async def ws_crystal(ws: WebSocket):
    await ws.accept()
    _web_clients.add(ws)
    logger.info("[Crystal] web client connected, total=%d", len(_web_clients))
    try:
        await ws.send_text(json.dumps({"type": "sleep_flow", **_sleep_flow}, ensure_ascii=False))
        await ws.send_text(json.dumps(_current_state, ensure_ascii=False))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _web_clients.discard(ws)
        logger.info("[Crystal] web client disconnected, total=%d", len(_web_clients))
