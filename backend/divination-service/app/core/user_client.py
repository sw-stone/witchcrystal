"""
User-service client for divination-service.

Fetches user profile data (MBTI type, nickname, etc.) from user-service
so that divination readings can be personalized.

Treated as an enhancement layer: if user-service is unavailable,
readings proceed without profile context.
"""
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class UserServiceClient:
    """HTTP client for the user-service (port 3002).

    Fetches user profile data for personalizing divination readings.
    HTTP client is created lazily.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = (
            base_url
            or os.environ.get("USER_SERVICE_URL", "http://localhost:3002")
        ).rstrip("/")
        self._client = client

    @property
    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=5.0)
        return self._client

    def get_profile(self, user_id: str) -> Optional[dict]:
        """Fetch a user's profile. Returns None if unavailable."""
        try:
            resp = self._http.get(f"/users/{user_id}")
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception as exc:
            logger.debug("[UserService] get_profile failed (degraded): %s", exc)
            return None
