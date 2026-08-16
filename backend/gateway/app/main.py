"""
API 网关 —— 对应 TASKTODO 目录结构中的 backend/gateway：
"API 网关 / 统一鉴权 / 路由"

范围：
- HTTP 反向代理：按路由表把请求转发到对应微服务
- WebSocket 透传：/ws/{user_id} 双向转发到 social-service
- 统一鉴权（Task 3.0）：网关层校验 Authorization: Bearer <access_token>，
  合法则注入 X-User-Id / X-User-Role 头透传给下游；
  公共路径（/health /auth/register /auth/login 等）放行。
"""
import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Union

# 加载 .env 文件（开发环境）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import httpx
import websockets
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.auth_jwt import (
    extract_bearer_token,
    is_public_path,
    verify_access_token,
)
from app.device_handler import router as device_router
from app.llm_config import router as llm_router
from app.mcp_server import router as mcp_router
from app.crystal_ball import router as crystal_router
from app.voice import router as voice_router
from app.routes import build_routes, match_route, social_ws_base_url
from app.tuya_handler import router as tuya_router

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="gateway", version="0.3.0")
app.include_router(tuya_router)
app.include_router(device_router)
app.include_router(llm_router)
app.include_router(mcp_router)
app.include_router(crystal_router)
app.include_router(voice_router)

_routes = build_routes()
_client = httpx.AsyncClient(timeout=30.0)

_CONSOLE_HTML = Path(__file__).parent / "static" / "console.html"
_CRYSTAL_HTML = Path(__file__).parent / "static" / "crystal-ball.html"
_TAROT_HTML = Path(__file__).parent / "static" / "tarot.html"
_SLEEP_ISLE_HTML = Path(__file__).parent / "static" / "sleep-isle.html"

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}

_USER_INJECTION_HEADERS = {"x-user-id", "x-user-role", "x-user-is-minor"}


async def _authenticate(request: Request) -> Tuple[bool, Optional[Response]]:
    """统一鉴权（Task 3.0）"""
    path = request.url.path
    if is_public_path(path):
        return True, None

    auth_header = request.headers.get("authorization", "")
    token = extract_bearer_token(auth_header)
    if token is None:
        return False, JSONResponse(
            status_code=401,
            content={"detail": "missing or malformed Authorization header"},
        )

    claims = verify_access_token(token)
    if claims is None:
        return False, JSONResponse(
            status_code=401,
            content={"detail": "token invalid or expired"},
        )
    request.state.user_id = claims.user_id
    request.state.user_role = claims.role
    request.state.user_is_minor = claims.is_minor
    return True, None


def _filter_headers(headers) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP}


def _inject_user_headers(request: Request, headers: dict) -> dict:
    """剥离外部伪造的 X-User-* 头，注入网关权威值"""
    filtered = {k: v for k, v in headers.items() if k.lower() not in _USER_INJECTION_HEADERS}
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        filtered["X-User-Id"] = user_id
        filtered["X-User-Role"] = getattr(request.state, "user_role", "user")
        filtered["X-User-Is-Minor"] = "true" if getattr(request.state, "user_is_minor", False) else "false"
    return filtered


@app.get("/health")
async def health():
    return {"status": "ok", "routes": [r.name for r in _routes]}


@app.get("/")
async def console():
    return FileResponse(_CONSOLE_HTML, media_type="text/html")


@app.get("/crystal")
async def crystal_ball_page():
    """水晶球动画页（手机端打开，实时显示模式/聆听状态）"""
    return FileResponse(_CRYSTAL_HTML, media_type="text/html")


@app.get("/tarot")
async def tarot_aura_page():
    """Tarot Aura · Soft Lumina 塔罗占卜 Web 应用（v4 柔光舒缓版样机落地）"""
    return FileResponse(_TAROT_HTML, media_type="text/html")


@app.get("/sleep-isle")
async def sleep_isle_page():
    """屿眠 Sleep Isle 主控页（手机插底座后打开；摇杆信号经 WS 驱动产品链路）"""
    return FileResponse(_SLEEP_ISLE_HTML, media_type="text/html")


# 静态资源（塔罗牌图片等）——不需要鉴权
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(request: Request, path: str):
    ok, err = await _authenticate(request)
    if not ok:
        return err

    full_path = "/" + path
    route = match_route(_routes, full_path)
    if route is None:
        return Response(
            status_code=404,
            content=f'{{"detail":"no route for {full_path}"}}',
            media_type="application/json",
        )

    upstream_url = route.base_url + full_path
    body = await request.body()
    forwarded_headers = _inject_user_headers(request, _filter_headers(request.headers))
    logger.info(
        "[Reasoning] 网关转发：%s %s -> %s（命中路由 %s，用户=%s）",
        request.method, full_path, upstream_url, route.name,
        getattr(request.state, "user_id", "anon"),
    )

    # Streaming SSE passthrough — don't buffer, relay bytes as they arrive.
    # This is required for /divination/tarot/interpret-stream to feel live.
    if full_path == "/divination/tarot/interpret-stream":
        return await _stream_proxy(request, upstream_url, body, forwarded_headers)

    try:
        upstream_resp = await _client.request(
            request.method,
            upstream_url,
            params=request.query_params,
            content=body if body else None,
            headers=forwarded_headers,
        )
    except httpx.RequestError as exc:
        logger.error("upstream %s unreachable: %s", route.name, exc)
        return Response(
            status_code=502,
            content=f'{{"detail":"upstream {route.name} unreachable"}}',
            media_type="application/json",
        )

    return Response(
        status_code=upstream_resp.status_code,
        content=upstream_resp.content,
        headers=_filter_headers(upstream_resp.headers),
    )


async def _stream_proxy(request: Request, upstream_url: str, body: bytes, headers: dict):
    """Relay an upstream response to the client chunk-by-chunk without buffering.

    Used for SSE endpoints (text/event-stream) so the browser receives tokens
    as the LLM generates them. Falls back to a normal buffered Response if the
    upstream isn't actually a stream.
    """
    try:
        # We need the status/headers BEFORE we return the StreamingResponse, but
        # they only become available once the stream starts. Use a one-shot
        # wrapper that captures them from the first yield.
        captured = {}

        async def capture_and_relay():
            timeout = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    request.method, upstream_url,
                    params=request.query_params,
                    content=body if body else None,
                    headers=headers,
                ) as upstream_resp:
                    captured["status"] = upstream_resp.status_code
                    captured["headers"] = _filter_headers(upstream_resp.headers)
                    async for chunk in upstream_resp.aiter_raw():
                        yield chunk

        gen = capture_and_relay()
        # Peek the first chunk to learn status/headers.
        first_chunk = await gen.__anext__()

        async def body_iter():
            yield first_chunk
            async for c in gen:
                yield c

        return StreamingResponse(
            body_iter(),
            status_code=captured.get("status", 200),
            headers=captured.get("headers", {"Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no"}),
        )
    except httpx.RequestError as exc:
        logger.error("stream upstream unreachable: %s", exc)
        return Response(
            status_code=502,
            content=f'{{"detail":"upstream stream unreachable"}}',
            media_type="application/json",
        )


@app.websocket("/ws/{user_id}")
async def ws_proxy(client_ws: WebSocket, user_id: str):
    """
    WebSocket 透传：App <-> gateway <-> social-service。
    NFC 碰一碰后的 friend_request_received / friend_request_accepted
    实时推送经此通道到达 App。
    """
    await client_ws.accept()
    upstream_url = f"{social_ws_base_url()}/ws/{user_id}"
    logger.info("[Reasoning] WS 透传建立：user=%s -> %s", user_id, upstream_url)
    try:
        async with websockets.connect(upstream_url) as upstream_ws:
            import asyncio

            async def client_to_upstream():
                while True:
                    text = await client_ws.receive_text()
                    await upstream_ws.send(text)

            async def upstream_to_client():
                async for message in upstream_ws:
                    await client_ws.send_text(
                        message if isinstance(message, str) else message.decode()
                    )

            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(client_to_upstream()),
                    asyncio.create_task(upstream_to_client()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except (WebSocketDisconnect, websockets.ConnectionClosed):
        pass
    except OSError:
        logger.error("ws upstream social-service unreachable for user %s", user_id)
    finally:
        try:
            await client_ws.close()
        except RuntimeError:
            pass  # 已关闭
