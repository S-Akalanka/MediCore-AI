from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, text

from nawaloka.config import get_secret


def _normalise_url(url: str) -> str:
    """Point plain postgres URLs at the psycopg driver."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a shared SQLAlchemy engine."""
    return create_engine(_normalise_url(get_secret("DATABASE_URL")), pool_pre_ping=True)


def run_query(sql: str, params: dict[str, Any] | None = None, timeout_ms: int = 15000) -> list[dict[str, Any]]:
    """Execute a SQL statement with optional bind parameters in a read-only transaction and return rows as dicts."""
    with get_engine().connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL statement_timeout = {int(timeout_ms)}"))
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]
