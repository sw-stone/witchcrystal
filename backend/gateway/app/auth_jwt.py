"""
网关内嵌的 JWT 校验 —— 不依赖 user-service 的 app 包（避免命名冲突）。

实现与 user-service/app/auth/jwt.py 完全一致（同样的 HS256 + JWT_SECRET），
故意复制而不是 import，因为：
1. gateway 有自己的 app 包，sys.path 注入会导致 app 命名空间冲突
2. JWT 校验逻辑足够薄（< 100 行），复制成本低于共享模块的复杂性
3. 两边读相同的 JWT_SECRET 环境变量即可保持密钥同步

如果将来 JWT 逻辑复杂化（如 RS256 / JWE），可抽出独立 pip 包。
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-in-prod-0xCAFEBABE")
JWT_ALG = "HS256"
JWT_LEEWAY_SEC = 30

PUBLIC_PATHS = {
    "/", "/health", "/auth/register", "/auth/login",
    "/auth/refresh", "/auth/service-token", "/docs", "/openapi.json",
    "/tuya/callback", "/device/touch-report", "/static",
    # 静态 Web 应用入口页（显式 GET 路由，但 catch-all 鉴权会拦，需显式放行）
    "/crystal", "/tarot", "/sleep-isle",
    # 屿眠 Sleep Isle 链路：硬件信号 / 软件信号 / 状态查询（ESP32 与页面均匿名访问）
    "/device/signal", "/app/signal", "/sleep-flow",
    # Public AI tarot endpoints (server-side key, used by the showcase site).
    "/divination/tarot/interpret-stream", "/divination/tarot/card-reading",
    "/divination/tarot/cards",
    # Tarot Aura web app: anonymous history save/diary (keyed by client UID)
    "/divination/history",
    # LLM active config：设备端拉取当前启用 provider（含 api_key）。
    # 管理接口 /llm/providers* 仍需鉴权。
    "/llm/active", "/llm/chat", "/llm/tts",
    # MCP server：暴露 5 模式工具给外部 AI 客户端
    "/mcp",
    # 水晶球状态同步：ESP32 上报 / web WS / 命令下发
    "/device/state", "/device/command",
    "/ws/crystal",
    # 语音对话端点：ASR / TTS / LLM SSE 流式
    "/voice/asr", "/voice/tts", "/voice/chat-stream", "/voice/active",
}


@dataclass
class TokenClaims:
    user_id: str
    role: str
    is_minor: bool = False
    issued_at: int = 0
    expires_at: int = 0

    def as_dict(self) -> dict:
        return {
            "userId": self.user_id,
            "role": self.role,
            "isMinor": self.is_minor,
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
        }


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(message: str) -> str:
    sig = hmac.new(JWT_SECRET.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(sig)


def issue_access_token(
    user_id: str, role: str = "user", is_minor: bool = False,
    ttl_sec: Optional[int] = None,
) -> tuple[str, int]:
    """网关侧测试用：签发 access_token（生产环境由 user-service 签发）"""
    import uuid
    now = int(time.time())
    ttl = ttl_sec if ttl_sec is not None else 3600
    exp = now + ttl
    payload = {
        "sub": user_id, "role": role, "is_minor": is_minor,
        "iat": now, "exp": exp, "typ": "access",
        "jti": uuid.uuid4().hex,
    }
    header = {"alg": JWT_ALG, "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"
    sig_b64 = _sign(signing_input)
    return f"{signing_input}.{sig_b64}", exp


def verify_access_token(token: str) -> Optional[TokenClaims]:
    """校验 access_token 并返回 claims；失败返回 None"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"

        expected_sig = _sign(signing_input)
        if not hmac.compare_digest(expected_sig, sig_b64):
            logger.warning("[Reasoning] JWT 签名校验失败")
            return None

        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("typ") != "access":
            return None

        now = int(time.time())
        exp = payload.get("exp", 0)
        if exp + JWT_LEEWAY_SEC < now:
            logger.warning("[Reasoning] JWT 已过期")
            return None

        return TokenClaims(
            user_id=payload["sub"],
            role=payload.get("role", "user"),
            is_minor=payload.get("is_minor", False),
            issued_at=payload.get("iat", 0),
            expires_at=exp,
        )
    except Exception as exc:
        logger.warning("[Reasoning] JWT 解析异常: %s", exc)
        return None


def extract_bearer_token(authorization_header: str) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    for p in PUBLIC_PATHS:
        if path.startswith(p + "/"):
            return True
    return False
