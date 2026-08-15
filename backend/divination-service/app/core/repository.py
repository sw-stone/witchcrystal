"""
Divination record repository — in-memory implementation.

Default when DATABASE_URL is not set. Zero dependencies, fast for dev/testing.
Upgrades to Postgres via pg_repository.py when DATABASE_URL is configured.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List


class DivinationRepository:
    """In-memory store for divination readings."""

    def __init__(self) -> None:
        self._records: List[dict] = []

    def create(self, record: dict) -> dict:
        """Insert a new divination record."""
        if "id" not in record:
            record["id"] = str(uuid.uuid4())
        if "created_at" not in record:
            record["created_at"] = datetime.now(timezone.utc).isoformat()
        self._records.append(record)
        return record

    def get_history(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get a user's divination history, newest first."""
        user_records = [r for r in self._records if r.get("user_id") == user_id]
        user_records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return user_records[:limit]

    def get_stats(self, user_id: str) -> dict:
        """Compute usage stats for a user."""
        user_records = [r for r in self._records if r.get("user_id") == user_id]
        type_counts: dict = {}
        for r in user_records:
            t = r.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "user_id": user_id,
            "total_divinations": len(user_records),
            "by_type": type_counts,
        }

    def get_by_id(self, record_id: str) -> Optional[dict]:
        """Get a single record by ID."""
        for r in self._records:
            if r.get("id") == record_id:
                return r
        return None
