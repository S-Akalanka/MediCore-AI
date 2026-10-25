from typing import Any

from sqlalchemy import inspect, text

from nawaloka.db.client import get_engine


def _date_ranges(conn, table: str, columns: list[dict[str, Any]]) -> dict[str, tuple[Any, Any]]:
    date_columns = [c["name"] for c in columns if "DATE" in c["type"].upper() or "TIMESTAMP" in c["type"].upper()]
    if not date_columns:
        return {}
    selects = ", ".join(f'MIN("{c}"), MAX("{c}")' for c in date_columns)
    row = conn.execute(text(f'SELECT {selects} FROM "{table}"')).fetchone()
    return {c: (row[2 * i], row[2 * i + 1]) for i, c in enumerate(date_columns)}


def get_schema(sample_rows: int = 3, date_ranges: bool = False) -> dict[str, Any]:
    """Introspect tables, columns, keys and sample rows from the live database."""
    engine = get_engine()
    inspector = inspect(engine)
    schema: dict[str, Any] = {}
    with engine.connect() as conn:
        for table in sorted(inspector.get_table_names()):
            columns = [
                {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
                for c in inspector.get_columns(table)
            ]
            primary_key = inspector.get_pk_constraint(table).get("constrained_columns", [])
            foreign_keys = [
                {
                    "columns": fk["constrained_columns"],
                    "ref_table": fk["referred_table"],
                    "ref_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table)
            ]
            rows = conn.execute(text(f'SELECT * FROM "{table}" LIMIT {int(sample_rows)}'))
            samples = [dict(r._mapping) for r in rows]
            ranges = _date_ranges(conn, table, columns) if date_ranges else {}
            schema[table] = {
                "columns": columns,
                "primary_key": primary_key,
                "foreign_keys": foreign_keys,
                "samples": samples,
                "date_ranges": ranges,
            }
    return schema
