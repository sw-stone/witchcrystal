"""
Community sharing — share divination results, browse others' shared results.
Uses factory pattern: in-memory by default, Postgres when DATABASE_URL is set.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional


class CommunityStore:
    """In-memory community shares store."""

    def __init__(self) -> None:
        self._shares: list[dict] = []

    def share(self, user_id: str, nickname: str, divination_id: str,
              div_type: str, question: str, interpretation: str,
              cards: Optional[list] = None) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "nickname": nickname,
            "divination_id": divination_id,
            "type": div_type,
            "question": (question or "")[:100],
            "interpretation": interpretation,
            "cards": cards,
            "likes": 0,
            "liked_by": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._shares.append(entry)
        return entry

    def list_public(self, limit: int = 50, offset: int = 0) -> list[dict]:
        sorted_shares = sorted(self._shares, key=lambda x: x["created_at"], reverse=True)
        return sorted_shares[offset:offset + limit]

    def like(self, share_id: str, user_id: str) -> Optional[dict]:
        for s in self._shares:
            if s["id"] == share_id:
                if user_id not in s["liked_by"]:
                    s["liked_by"].append(user_id)
                    s["likes"] += 1
                return s
        return None

    def get_by_id(self, share_id: str) -> Optional[dict]:
        for s in self._shares:
            if s["id"] == share_id:
                return s
        return None

    def get_user_shares(self, user_id: str) -> list[dict]:
        return [s for s in self._shares if s["user_id"] == user_id]


# Module-level store via factory
from .factory import get_community_store as _get_store

def _store():
    return _get_store()


def share_divination(user_id: str, nickname: str, divination_id: str,
                     div_type: str, question: str, interpretation: str,
                     cards: list = None) -> dict:
    return _store().share(user_id, nickname, divination_id,
                          div_type, question, interpretation, cards)


def list_public_shares(limit: int = 50, offset: int = 0) -> list[dict]:
    return _store().list_public(limit=limit, offset=offset)


def like_share(share_id: str, user_id: str):
    return _store().like(share_id, user_id)


def get_share(share_id: str):
    return _store().get_by_id(share_id)


def get_user_shares(user_id: str):
    return _store().get_user_shares(user_id)
