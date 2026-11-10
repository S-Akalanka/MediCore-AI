from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy import inspect, text

from nawaloka.db.client import get_engine

MAX_WORKERS = 8


def _date_ranges(conn, table: str, columns: list[dict[str, Any]]) -> dict[str, tuple[Any, Any]]:
    date_columns = [c["name"] for c in columns if "DATE" in c["type"].upper() or "TIMESTAMP" in c["type"].upper()]
    if not date_columns:
        return {}
    selects = ", ".join(f'MIN("{c}"), MAX("{c}")' for c in date_columns)
    row = conn.execute(text(f'SELECT {selects} FROM "{table}"')).fetchone()
    return {c: (row[2 * i], row[2 * i + 1]) for i, c in enumerate(date_columns)}


def _table_data(table: str, columns: list[dict[str, Any]], sample_rows: int, date_ranges: bool):
    """Fetch sample rows and date ranges for one table on its own connection."""
    with get_engine().connect() as conn:
        samples = []
        if sample_rows:
            rows = conn.execute(text(f'SELECT * FROM "{table}" LIMIT {int(sample_rows)}'))
            samples = [dict(r._mapping) for r in rows]
        ranges = _date_ranges(conn, table, columns) if date_ranges else {}
    return samples, ranges


def get_schema(sample_rows: int = 3, date_ranges: bool = False) -> dict[str, Any]:
    """Introspect tables, columns, keys, sample rows and date ranges from the live database."""
    inspector = inspect(get_engine())
    raw_columns = inspector.get_multi_columns()
    raw_pks = inspector.get_multi_pk_constraint()
    raw_fks = inspector.get_multi_foreign_keys()

    schema: dict[str, Any] = {}
    for key in sorted(raw_columns, key=lambda k: k[1]):
        table = key[1]
        schema[table] = {
            "columns": [
                {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]} for c in raw_columns[key]
            ],
            "primary_key": raw_pks.get(key, {}).get("constrained_columns", []),
            "foreign_keys": [
                {
                    "columns": fk["constrained_columns"],
                    "ref_table": fk["referred_table"],
                    "ref_columns": fk["referred_columns"],
                }
                for fk in raw_fks.get(key, [])
            ],
            "samples": [],
            "date_ranges": {},
        }

    if sample_rows or date_ranges:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                table: pool.submit(_table_data, table, info["columns"], sample_rows, date_ranges)
                for table, info in schema.items()
            }
            for table, future in futures.items():
                schema[table]["samples"], schema[table]["date_ranges"] = future.result()
    return schema
