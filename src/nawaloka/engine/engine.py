from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from nawaloka.config import SQL_MAX_RETRIES
from nawaloka.db.client import run_query
from nawaloka.db.schema import get_schema
from nawaloka.engine.generator import generate_sql
from nawaloka.engine.validator import validate_sql

BLOCKED_MESSAGE = "I can only read data. Requests that change or delete records are not allowed."
FAILED_MESSAGE = (
    "I could not turn that into a working query. "
    "Could you rephrase it or add more detail, such as a time range or a department name?"
)


@dataclass
class EngineResult:
    status: str
    question: str
    sql: str = ""
    rows: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    attempts: int = 0


_schema_cache: dict | None = None


def _schema() -> dict:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_schema(sample_rows=0)
    return _schema_cache


def ask(question: str) -> EngineResult:
    """Run the full NL2SQL loop: generate, validate, execute, retry on failure."""
    previous_sql, error = "", ""
    for attempt in range(1, SQL_MAX_RETRIES + 1):
        try:
            generation = generate_sql(question, previous_sql, error)
        except Exception as exc:
            logger.error("Generation failed: {}", exc)
            return EngineResult("failed", question, message=FAILED_MESSAGE, attempts=attempt)

        if generation.clarification and not generation.sql:
            return EngineResult("clarification", question, message=generation.clarification, attempts=attempt)

        validation = validate_sql(generation.sql, _schema())
        if validation.blocked:
            logger.warning("Blocked SQL: {}", generation.sql)
            return EngineResult("blocked", question, sql=generation.sql, message=BLOCKED_MESSAGE, attempts=attempt)
        if not validation.ok:
            previous_sql, error = generation.sql, "; ".join(validation.errors)
            logger.warning("Attempt {} failed validation: {}", attempt, error)
            continue

        try:
            rows = run_query(validation.sql)
        except Exception as exc:
            previous_sql, error = validation.sql, str(exc).splitlines()[0]
            logger.warning("Attempt {} failed execution: {}", attempt, error)
            continue

        return EngineResult("ok", question, sql=validation.sql, rows=rows, attempts=attempt)

    return EngineResult("failed", question, sql=previous_sql, message=FAILED_MESSAGE, attempts=SQL_MAX_RETRIES)
