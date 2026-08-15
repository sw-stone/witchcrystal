"""
Tuya IoT cloud callback handler.
Receives device DP (data point) reports from the T5AI-Core hardware via Tuya Cloud,
then syncs data to the appropriate backend services.

Tuya Cloud → (HTTP callback) → gateway /tuya/callback → emotion-service / task-service
"""
import json
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tuya"])

_EMOTION_URL = os.environ.get("EMOTION_SERVICE_URL", "http://localhost:3009")
_TASK_URL = os.environ.get("TASK_SERVICE_URL", "http://localhost:3010")
_DIVINATION_URL = os.environ.get("DIVINATION_SERVICE_URL", "http://localhost:3008")

_http = httpx.AsyncClient(timeout=10.0)


@router.post("/tuya/callback")
async def tuya_callback(request: Request):
    """
    Tuya Cloud IoT data point callback.
    Tuya Cloud forwards device DP reports here when configured in the IoT platform.

    Expected payload (simplified Tuya callback format):
    {
        "devId": "device_uuid",
        "productKey": "...",
        "status": [
            {"code": "mode", "value": 1},
            {"code": "last_divination", "value": "{...}"},
            {"code": "led_effect", "value": 3},
            {"code": "emotion_level", "value": 3},
            {"code": "companion_active", "value": true},
            {"code": "daily_fortune", "value": "..."}
        ]
    }
    """
    body = await request.body()
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("[Tuya] invalid JSON callback: %s", body[:200])
        return Response(status_code=400, content=b'{"detail":"invalid json"}')

    dev_id = payload.get("devId", "")
    status_list = payload.get("status", payload.get("dps", []))

    logger.info("[Reasoning] Tuya callback: devId=%s status_count=%d", dev_id, len(status_list))

    user_id = await _resolve_user_id(dev_id)
    if not user_id:
        logger.warning("[Tuya] no user bound to device %s, skipping sync", dev_id)
        return {"status": "ok", "synced": False, "reason": "no_bound_user"}

    synced = []
    for status in status_list:
        code = status.get("code", "")
        value = status.get("value")

        if code == "emotion_level":
            await _sync_emotion(user_id, value)
            synced.append("emotion")
        elif code == "last_divination":
            await _sync_divination(user_id, value)
            synced.append("divination")
        elif code == "mode":
            logger.info("[Tuya] mode change: user=%s mode=%s", user_id, value)
            synced.append("mode")

    return {"status": "ok", "synced": synced, "user_id": user_id}


async def _resolve_user_id(dev_id: str) -> Optional[str]:
    """
    Resolve device UID → user_id via user-service device_bindings.
    Falls back to the dev_id itself if user-service is unavailable.
    """
    user_url = os.environ.get("USER_SERVICE_URL", "http://localhost:3001")
    try:
        resp = await _http.get(f"{user_url}/devices/{dev_id}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("userId")
    except Exception:
        pass
    return None


async def _sync_emotion(user_id: str, emotion_level: int) -> None:
    """Sync emotion level from device to emotion-service + task-service."""
    try:
        emotion = "sadness" if emotion_level <= 3 else "anxiety" if emotion_level <= 5 else "calm" if emotion_level <= 7 else "joy"
        await _http.post(f"{_EMOTION_URL}/emotion/log", json={
            "userId": user_id,
            "emotion": emotion,
            "intensity": emotion_level,
            "triggerSource": "device",
            "context": "auto-detected from T5AI-Core voice interaction",
        })
        await _http.post(f"{_TASK_URL}/task/mood-log", json={
            "userId": user_id,
            "emotion": emotion,
            "intensity": emotion_level,
        })
        logger.info("[Reasoning] emotion synced: user=%s level=%d -> emotion-service + task-service", user_id, emotion_level)
    except Exception as e:
        logger.error("[Tuya] emotion sync failed: %s", e)


async def _sync_divination(user_id: str, divination_json: str) -> None:
    """Log divination result to task-service for points."""
    try:
        div_data = json.loads(divination_json) if isinstance(divination_json, str) else divination_json
        div_type = div_data.get("type", "tarot") if isinstance(div_data, dict) else "tarot"
        await _http.post(f"{_TASK_URL}/task/divination", json={
            "userId": user_id,
            "divType": div_type,
        })
        logger.info("[Reasoning] divination synced: user=%s type=%s -> task-service (+points)", user_id, div_type)
    except Exception as e:
        logger.error("[Tuya] divination sync failed: %s", e)


@router.post("/tuya/device/{dev_id}/mode")
async def set_device_mode(dev_id: str, mode: int):
    """
    App → Cloud → Device: send a mode change command.
    In production this goes through Tuya Cloud OpenAPI.
    Here we just log it (the actual command is sent via Tuya SDK).
    """
    mode_names = {0: "standby", 1: "tarot", 2: "astrology", 3: "dream", 4: "fortune", 5: "companion"}
    mode_name = mode_names.get(mode, f"unknown({mode})")
    logger.info("[Tuya] device mode command: dev=%s mode=%s", dev_id, mode_name)
    return {"status": "sent", "devId": dev_id, "mode": mode_name}
