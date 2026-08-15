"""
Divination record repository — PostgreSQL implementation.

Activated when DATABASE_URL environment variable is set.
Uses psycopg3 with connection pooling, matching the pattern in user-service.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

import psycopg
from psycopg_pool import ConnectionPool

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS divination_records (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL,
    type         TEXT NOT NULL,
    question     TEXT,
    cards        JSONB,
    interpretation TEXT,
    zodiac       JSONB,
    emotion_before TEXT,
    emotion_after  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_div_records_user ON divination_records(user_id);
CREATE INDEX IF NOT EXISTS idx_div_records_type ON divination_records(type);
CREATE INDEX IF NOT EXISTS idx_div_records_created ON divination_records(created_at DESC);
"""

_CREATE_SHARES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS divination_shares (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    nickname       TEXT,
    divination_id  TEXT,
    type           TEXT NOT NULL,
    question       TEXT,
    interpretation TEXT,
    cards          JSONB,
    likes          INTEGER NOT NULL DEFAULT 0,
    liked_by       JSONB NOT NULL DEFAULT '[]',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_div_shares_created ON divination_shares(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_div_shares_user ON divination_shares(user_id);
"""


class PostgresDivinationRepository:
    """PostgreSQL-backed divination record store."""

    def __init__(self, database_url: str, pool: ConnectionPool) -> None:
        self._database_url = database_url
        self._pool = pool
        self._init_tables()

    def _init_tables(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            conn.execute(_CREATE_SHARES_TABLE_SQL)
            conn.commit()

    def create(self, record: dict) -> dict:
        if "id" not in record:
            record["id"] = str(uuid.uuid4())
        if "created_at" not in record:
            record["created_at"] = datetime.now(timezone.utc).isoformat()

        with self._pool.connection() as conn:
            conn.execute(
                """INSERT INTO divination_records
                   (id, user_id, type, question, cards, interpretation,
                    zodiac, emotion_before, emotion_after, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    record["id"],
                    record.get("user_id", ""),
                    record.get("type", ""),
                    record.get("question"),
                    json.dumps(record.get("cards")) if record.get("cards") else None,
                    record.get("interpretation"),
                    json.dumps(record.get("zodiac")) if record.get("zodiac") else None,
                    record.get("emotion_before"),
                    record.get("emotion_after"),
                    record.get("created_at"),
                ),
            )
            conn.commit()
        return record

    def get_history(self, user_id: str, limit: int = 20) -> List[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT id, user_id, type, question, cards, interpretation,
                          zodiac, emotion_before, emotion_after, created_at
                   FROM divination_records
                   WHERE user_id = %s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (user_id, limit),
            )
            rows = cur.fetchall()
            return [self._row_to_dict(r, cur) for r in rows]

    def get_stats(self, user_id: str) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT type, COUNT(*) as cnt
                   FROM divination_records
                   WHERE user_id = %s
                   GROUP BY type""",
                (user_id,),
            )
            type_counts = {row[0]: row[1] for row in cur.fetchall()}

            cur = conn.execute(
                "SELECT COUNT(*) FROM divination_records WHERE user_id = %s",
                (user_id,),
            )
            total = cur.fetchone()[0]

        return {
            "user_id": user_id,
            "total_divinations": total,
            "by_type": type_counts,
        }

    def get_by_id(self, record_id: str) -> Optional[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT id, user_id, type, question, cards, interpretation,
                          zodiac, emotion_before, emotion_after, created_at
                   FROM divination_records WHERE id = %s""",
                (record_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_dict(row, cur)

    @staticmethod
    def _row_to_dict(row, cur) -> dict:
        cols = [desc[0] for desc in cur.description]
        d = dict(zip(cols, row))
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat() if hasattr(d["created_at"], "isoformat") else str(d["created_at"])
        for json_field in ("cards", "zodiac"):
            if d.get(json_field) and isinstance(d[json_field], str):
                try:
                    d[json_field] = json.loads(d[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d


class PostgresCommunityStore:
    """PostgreSQL-backed community shares store."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def share(self, user_id: str, nickname: str, divination_id: str,
              div_type: str, question: str, interpretation: str,
              cards: Optional[list] = None) -> dict:
        share_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with self._pool.connection() as conn:
            conn.execute(
                """INSERT INTO divination_shares
                   (id, user_id, nickname, divination_id, type, question,
                    interpretation, cards, likes, liked_by, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, '[]', %s)""",
                (share_id, user_id, nickname, divination_id, div_type,
                 (question or "")[:100], interpretation,
                 json.dumps(cards) if cards else None, created_at),
            )
            conn.commit()
        return {
            "id": share_id, "user_id": user_id, "nickname": nickname,
            "divination_id": divination_id, "type": div_type,
            "question": (question or "")[:100], "interpretation": interpretation,
            "cards": cards, "likes": 0, "liked_by": [], "created_at": created_at,
        }

    def list_public(self, limit: int = 50, offset: int = 0) -> List[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT id, user_id, nickname, divination_id, type, question,
                          interpretation, cards, likes, liked_by, created_at
                   FROM divination_shares
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (limit, offset),
            )
            return [self._row_to_dict(r, cur) for r in cur.fetchall()]

    def like(self, share_id: str, user_id: str) -> Optional[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                "SELECT liked_by FROM divination_shares WHERE id = %s",
                (share_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            liked_by = row[0] if isinstance(row[0], list) else json.loads(row[0] or "[]")
            if user_id not in liked_by:
                liked_by.append(user_id)
                conn.execute(
                    """UPDATE divination_shares
                       SET likes = %s, liked_by = %s WHERE id = %s""",
                    (len(liked_by), json.dumps(liked_by), share_id),
                )
                conn.commit()
            cur = conn.execute(
                """SELECT id, user_id, nickname, divination_id, type, question,
                          interpretation, cards, likes, liked_by, created_at
                   FROM divination_shares WHERE id = %s""",
                (share_id,),
            )
            row = cur.fetchone()
            return self._row_to_dict(row, cur) if row else None

    def get_by_id(self, share_id: str) -> Optional[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT id, user_id, nickname, divination_id, type, question,
                          interpretation, cards, likes, liked_by, created_at
                   FROM divination_shares WHERE id = %s""",
                (share_id,),
            )
            row = cur.fetchone()
            return self._row_to_dict(row, cur) if row else None

    def get_user_shares(self, user_id: str) -> List[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                """SELECT id, user_id, nickname, divination_id, type, question,
                          interpretation, cards, likes, liked_by, created_at
                   FROM divination_shares WHERE user_id = %s
                   ORDER BY created_at DESC""",
                (user_id,),
            )
            return [self._row_to_dict(r, cur) for r in cur.fetchall()]

    @staticmethod
    def _row_to_dict(row, cur) -> dict:
        cols = [desc[0] for desc in cur.description]
        d = dict(zip(cols, row))
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat() if hasattr(d["created_at"], "isoformat") else str(d["created_at"])
        for json_field in ("cards", "liked_by"):
            if d.get(json_field) and isinstance(d[json_field], str):
                try:
                    d[json_field] = json.loads(d[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
