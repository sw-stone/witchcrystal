"""
Repository factory — switches between in-memory and PostgreSQL based on DATABASE_URL.

Pattern mirrors user-service/factory.py:
- No DATABASE_URL → in-memory (zero deps, fast dev/testing)
- DATABASE_URL set → Postgres with connection pool
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_pool: Optional[object] = None
_divination_repo: Optional[object] = None
_community_store: Optional[object] = None


def _get_pool(database_url: str):
    """Get or create a shared connection pool."""
    global _pool
    if _pool is not None:
        return _pool
    from psycopg_pool import ConnectionPool
    _pool = ConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=5,
        open=True,
    )
    logger.info("[DB] Postgres connection pool created")
    return _pool


def get_divination_repository():
    """Return a cached divination repository based on environment."""
    global _divination_repo
    if _divination_repo is not None:
        return _divination_repo

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        from .repository import DivinationRepository
        _divination_repo = DivinationRepository()
    else:
        from .pg_repository import PostgresDivinationRepository
        _divination_repo = PostgresDivinationRepository(database_url, pool=_get_pool(database_url))
    return _divination_repo


def get_community_store():
    """Return a cached community store based on environment."""
    global _community_store
    if _community_store is not None:
        return _community_store

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        from .community import CommunityStore
        _community_store = CommunityStore()
    else:
        from .pg_repository import PostgresCommunityStore
        _community_store = PostgresCommunityStore(pool=_get_pool(database_url))
    return _community_store
