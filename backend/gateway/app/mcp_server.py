"""
MCP Server (HTTP) —— 把水晶球 5 大模式能力暴露为标准 MCP 工具。

协议：JSON-RPC 2.0 over HTTP（MCP Streamable HTTP transport）
  POST /mcp  body = {"jsonrpc":"2.0","id":N,"method":"tools/list"|"tools/call",...}

工具列表（与 ESP32 端 app_tools 一一对应，由网关转发到设备或直接占位）：
  - play_whitenoise / stop_audio / set_volume
  - start_breathing / stop_breathing
  - start_meditation / stop_meditation
  - draw_tarot / interpret_dream / get_horoscope
  - set_alarm / trigger_alarm_now / stop_alarm
  - set_mode / get_current_mode / set_led_effect

设备联动：网关通过 WebSocket /ws/devices/{device_id} 或 HTTP DP 下发指令到 ESP32。
当前 ESP32 端未接设备指令通道（沉淀待办），MCP 工具先返回占位结果，
待设备通道打通后改为真实下发。
"""
import json
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/mcp", tags=["mcp"])

# 工具定义（与 ESP32 app_tools_get_schema 同源，便于双端一致）
_MCP_TOOLS = [
    {"name": "play_whitenoise", "description": "启动白噪音助眠。type=white/pink/rain",
     "inputSchema": {"type": "object", "properties": {"type": {"type": "string", "enum": ["white", "pink", "rain"]}}, "required": []}},
    {"name": "stop_audio", "description": "停止当前声音", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "set_volume", "description": "调音量 0-100", "inputSchema": {"type": "object", "properties": {"level": {"type": "integer", "minimum": 0, "maximum": 100}}, "required": ["level"]}},
    {"name": "start_breathing", "description": "启动4-7-8呼吸引导", "inputSchema": {"type": "object", "properties": {"cycle_sec": {"type": "integer"}}, "required": []}},
    {"name": "stop_breathing", "description": "停止呼吸引导", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "start_meditation", "description": "启动冥想", "inputSchema": {"type": "object", "properties": {"duration_min": {"type": "integer", "minimum": 1, "maximum": 60}}, "required": []}},
    {"name": "stop_meditation", "description": "停止冥想", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "draw_tarot", "description": "抽塔罗牌。spread=single/three", "inputSchema": {"type": "object", "properties": {"spread": {"type": "string", "enum": ["single", "three"]}}, "required": []}},
    {"name": "interpret_dream", "description": "启动解梦氛围", "inputSchema": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}},
    {"name": "get_horoscope", "description": "查星座运势", "inputSchema": {"type": "object", "properties": {"sign": {"type": "string"}}, "required": ["sign"]}},
    {"name": "set_alarm", "description": "设闹钟 hour:minute", "inputSchema": {"type": "object", "properties": {"hour": {"type": "integer"}, "minute": {"type": "integer"}}, "required": ["hour", "minute"]}},
    {"name": "trigger_alarm_now", "description": "立即触发闹铃", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "stop_alarm", "description": "停止闹钟", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "set_mode", "description": "切模式 standby/whitenoise/breathing/meditation/divination/alarm", "inputSchema": {"type": "object", "properties": {"mode": {"type": "string", "enum": ["standby", "whitenoise", "breathing", "meditation", "divination", "alarm"]}}, "required": ["mode"]}},
    {"name": "get_current_mode", "description": "查当前模式", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "set_led_effect", "description": "切灯光 white/purple/gold/green/rainbow/midnight", "inputSchema": {"type": "object", "properties": {"effect": {"type": "string", "enum": ["white", "purple", "gold", "green", "rainbow", "midnight"]}}, "required": ["effect"]}},
]


def _ok(req_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _dispatch_tool(name: str, args: dict) -> str:
    """工具分发。当前占位返回（设备通道待接），后续改为下发到 ESP32。"""
    # TODO: 通过设备 WS/HTTP 通道下发到 ESP32 执行，返回真实结果
    # 当前：返回占位文本，让 MCP 客户端能跑通协议链路
    placeholders = {
        "play_whitenoise": lambda a: f"已启动{a.get('type', 'pink')}白噪音（占位：设备通道待接）",
        "stop_audio": lambda a: "声音已停止（占位）",
        "set_volume": lambda a: f"音量调至{a.get('level', 60)}%（占位）",
        "start_breathing": lambda a: "4-7-8 呼吸引导已启动（占位）",
        "stop_breathing": lambda a: "呼吸引导已停止（占位）",
        "start_meditation": lambda a: f"冥想已启动 {a.get('duration_min', 10)} 分钟（占位）",
        "stop_meditation": lambda a: "冥想已停止（占位）",
        "draw_tarot": lambda a: f"已抽{a.get('spread', 'single')}牌阵（占位：真实抽牌待设备通道）",
        "interpret_dream": lambda a: f"解梦氛围已启动，梦境：{a.get('content', '')}（占位）",
        "get_horoscope": lambda a: f"{a.get('sign', '?')}运势查询（占位）",
        "set_alarm": lambda a: f"闹钟已设 {a.get('hour', 0):02d}:{a.get('minute', 0):02d}（占位）",
        "trigger_alarm_now": lambda a: "闹铃已触发（占位）",
        "stop_alarm": lambda a: "闹钟已停止（占位）",
        "set_mode": lambda a: f"已切到{a.get('mode', '?')}模式（占位）",
        "get_current_mode": lambda a: "当前模式：待机（占位）",
        "set_led_effect": lambda a: f"灯光切到{a.get('effect', '?')}（占位）",
    }
    fn = placeholders.get(name)
    if not fn:
        return f"未知工具：{name}"
    return fn(args)


@router.post("")
@router.post("/")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 端点。
    支持 initialize / tools/list / tools/call 三种方法。"""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_err(None, -32700, "Parse error"))

    req_id = body.get("id")
    method = body.get("method", "")

    if method == "initialize":
        return JSONResponse(_ok(req_id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "crystal-ball-mcp", "version": "0.1.0"},
            "capabilities": {"tools": {}},
        }))

    if method == "tools/list":
        return JSONResponse(_ok(req_id, {"tools": _MCP_TOOLS}))

    if method == "tools/call":
        params = body.get("params", {})
        name = params.get("name", "")
        args = params.get("arguments", {}) or {}
        result_text = _dispatch_tool(name, args)
        return JSONResponse(_ok(req_id, {
            "content": [{"type": "text", "text": result_text}],
            "isError": False,
        }))

    return JSONResponse(_err(req_id, -32601, f"Method not found: {method}"))
