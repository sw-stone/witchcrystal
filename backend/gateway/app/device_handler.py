"""
设备直连上报模块 (Task 2.2a) —— SIM 卡/蜂窝网络方案。

当挂件自带 SIM 卡时，触碰后可直接通过 HTTP 上报双方 device_uid 到网关，
无需手机 App 代理。

鉴权方式：设备使用 product API key（与 App 的 JWT 不同），
通过 X-Device-Key 头验证。key 由 .env.local 的 DEVICE_API_KEY 配置。

数据流：
  [挂件A SIM] --HTTP--> gateway /device/touch-report --> social-service /nfc-touch
  [挂件B SIM]  (对方 device_uid 在触碰时通过 BLE/NFC 交换获知)
"""
import logging
import os

import httpx
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/device", tags=["device-direct"])

_DEVICE_API_KEY = os.environ.get("DEVICE_API_KEY", "")
_SOCIAL_URL = os.environ.get("SOCIAL_SERVICE_URL", "http://localhost:3002")
_http = httpx.AsyncClient(timeout=10.0)


class DeviceTouchReportDto(BaseModel):
    """设备直连上报的碰一碰事件（camelCase 输入）"""
    deviceUidA: str = Field(min_length=1)
    deviceUidB: str = Field(min_length=1)


class DeviceTouchReportResponse(BaseModel):
    """上报结果（camelCase 输出）"""
    status: str
    friendRequestCreated: bool = False
    message: str = ""


@router.post("/touch-report", response_model=DeviceTouchReportResponse)
async def device_touch_report(
    dto: DeviceTouchReportDto,
    x_device_key: str = Header(default="", alias="X-Device-Key"),
):
    """
    设备直连碰一碰上报（SIM 卡方案）。

    挂件通过蜂窝网络直接调用此端点，上报双方 device_uid。
    网关验证 device API key 后，转发给 social-service 的 /nfc-touch。

    鉴权：X-Device-Key 头需匹配环境变量 DEVICE_API_KEY。
    若 DEVICE_API_KEY 未配置，则放行（开发模式）。
    """
    if _DEVICE_API_KEY:
        if x_device_key != _DEVICE_API_KEY:
            logger.warning(
                "[Reasoning] 设备上报鉴权失败: device_a=%s key_prefix=%s",
                dto.deviceUidA,
                x_device_key[:8] if x_device_key else "(empty)",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid device API key",
            )
    else:
        logger.debug("[Reasoning] DEVICE_API_KEY 未配置，设备上报放行（开发模式）")

    logger.info(
        "[Reasoning] 设备直连碰一碰上报: a=%s b=%s",
        dto.deviceUidA,
        dto.deviceUidB,
    )

    try:
        resp = await _http.post(
            f"{_SOCIAL_URL}/nfc-touch",
            json={
                "deviceUidA": dto.deviceUidA,
                "deviceUidB": dto.deviceUidB,
            },
        )
    except httpx.RequestError as exc:
        logger.error("social-service unreachable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="social-service unreachable",
        )

    if resp.status_code == 429:
        return DeviceTouchReportResponse(
            status="cooldown",
            friendRequestCreated=False,
            message="触碰冷却中，请稍后再试",
        )

    if resp.status_code == 200:
        try:
            data = resp.json()
        except Exception:
            data = None
        created = data is not None
        return DeviceTouchReportResponse(
            status="ok",
            friendRequestCreated=created,
            message="好友申请已创建" if created else "无需创建（已是好友或隐私设置关闭）",
        )

    logger.error(
        "social-service /nfc-touch returned %d: %s",
        resp.status_code,
        resp.text[:200],
    )
    raise HTTPException(
        status_code=resp.status_code,
        detail=resp.text,
    )
