"""
路由表 —— API 网关的核心配置：请求路径前缀 -> 上游微服务。

设计要点：
- App 端只对接网关一个地址（默认 :3000），不需要知道 6 个微服务各自的端口。
- 匹配按"最长前缀优先"：/pets/{id}/chat 是 Agent 对话，必须先于 /pets 匹配到
  personality-engine，其余 /pets/** 才落到 pet-profile-service。
- memory-store 是 Agent 内部依赖（personality-engine 服务端调用），
  不对 App 暴露，因此路由表中刻意没有它。
"""
import os
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Route:
    name: str  # 上游服务名（用于日志/诊断）
    base_url: str  # 上游 base url
    pattern: re.Pattern  # 命中该路由的路径正则


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).rstrip("/")


def build_routes() -> list[Route]:
    user = _env("USER_SERVICE_URL", "http://localhost:3001")
    social = _env("SOCIAL_SERVICE_URL", "http://localhost:3002")
    pet = _env("PET_PROFILE_SERVICE_URL", "http://localhost:3003")
    diary = _env("DIARY_SERVICE_URL", "http://localhost:3004")
    personality = _env("PERSONALITY_ENGINE_URL", "http://localhost:3006")
    town = _env("TOWN_SIMULATION_URL", "http://localhost:3007")
    divination = _env("DIVINATION_SERVICE_URL", "http://localhost:3008")
    emotion = _env("EMOTION_SERVICE_URL", "http://localhost:3009")
    task = _env("TASK_SERVICE_URL", "http://localhost:3010")

    # 顺序即优先级：更具体的模式放前面
    return [
        Route("personality-engine", personality, re.compile(r"^/pets/[^/]+/chat$")),
        Route("pet-profile-service", pet, re.compile(r"^/(pets|shop)(/.*)?$")),
        Route("user-service", user, re.compile(r"^/(users|devices|auth)(/.*)?$")),
        Route(
            "social-service",
            social,
            re.compile(r"^/(nfc-touch|friend-requests|friends)(/.*)?$"),
        ),
        Route("diary-service", diary, re.compile(r"^/diary(/.*)?$")),
        Route("town-simulation", town, re.compile(r"^/town(/.*)?$")),
        Route("divination-service", divination, re.compile(r"^/divination(/.*)?$")),
        Route("emotion-service", emotion, re.compile(r"^/emotion(/.*)?$")),
        Route("task-service", task, re.compile(r"^/task(/.*)?$")),
    ]


def match_route(routes: list[Route], path: str) -> Optional[Route]:
    for route in routes:
        if route.pattern.match(path):
            return route
    return None


def social_ws_base_url() -> str:
    """WebSocket 透传目标（social-service 的 /ws/{user_id}），http -> ws 协议转换"""
    base = _env("SOCIAL_SERVICE_URL", "http://localhost:3002")
    return base.replace("http://", "ws://").replace("https://", "wss://")
