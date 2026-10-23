from typing import Any

from sqlalchemy import inspect, text

from nawaloka.db.client import get_engine


def get_schema(sample_rows: int = 3) -> dict[str, Any]:
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
            schema[table] = {
                "columns": columns,
                "primary_key": primary_key,
                "foreign_keys": foreign_keys,
                "samples": samples,
            }
    return schema
