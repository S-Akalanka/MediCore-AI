from loguru import logger
from sqlalchemy import text

from nawaloka.db.client import get_engine, run_query
from nawaloka.db.schema import get_schema
from nawaloka.log import setup_logging


def main() -> None:
    """Print tables, row counts, foreign keys and one sample row per table."""
    setup_logging()
    logger.info("Connected: {}", run_query("SELECT 1 AS ok")[0]["ok"] == 1)
    schema = get_schema(sample_rows=1)
    logger.info("Tables found: {}", len(schema))
    with get_engine().connect() as conn:
        for table, info in schema.items():
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            logger.info("{} rows={} columns={}", table, count, len(info["columns"]))
            for fk in info["foreign_keys"]:
                logger.info("  fk {} -> {}.{}", fk["columns"], fk["ref_table"], fk["ref_columns"])
            if info["samples"]:
                logger.info("  sample {}", info["samples"][0])


if __name__ == "__main__":
    main()
