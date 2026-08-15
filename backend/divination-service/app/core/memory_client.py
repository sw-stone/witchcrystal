"""
Memory-store client for divination-service.

Provides continuity-aware tarot readings by storing and retrieving past
divination episodes. Memory-store is treated as an enhancement layer:
if it's unavailable, the reading proceeds without memory context.
"""
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class MemoryStoreClient:
    """HTTP client for the memory-store service (port 3005).

    Uses ``user_id`` as the memory key (mapped to petId in the API)
    so that each user's divination history forms a separate memory space.

    HTTP client is created lazily to avoid connection overhead during
    tests / startup when memory-store may not be running.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = (
            base_url
            or os.environ.get("MEMORY_STORE_URL", "http://localhost:3005")
        ).rstrip("/")
        self._client = client

    @property
    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=5.0)
        return self._client

    def search(self, user_id: str, query: str, limit: int = 5) -> list:
        """Search a user's past divination memories by semantic relevance."""
        resp = self._http.post(
            f"/memories/by-pet/{user_id}/search",
            json={"query": query, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    def create(
        self,
        pet_id: str,
        content: str,
        kind: str = "episode",
        importance: int = 4,
        related_pet_id: Optional[str] = None,
    ) -> dict:
        """Create a new memory entry for a user's divination reading."""
        payload: dict = {
            "petId": pet_id,
            "content": content,
            "kind": kind,
            "importance": importance,
        }
        if related_pet_id is not None:
            payload["relatedPetId"] = related_pet_id
        resp = self._http.post("/memories", json=payload)
        resp.raise_for_status()
        return resp.json()
