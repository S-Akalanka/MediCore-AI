import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

from nawaloka.db.client import get_engine
from nawaloka.log import setup_logging


def main() -> None:
    """Run a SQL dump file against the configured database."""
    setup_logging()
    if len(sys.argv) != 2:
        logger.error("Usage: uv run python scripts/load_dump.py path/to/medicore_data.sql")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        logger.error("File not found: {}", path)
        sys.exit(1)
    raw = get_engine().raw_connection()
    try:
        with raw.cursor() as cur:
            executed = 0
            buffer: list[str] = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not buffer and (not line.strip() or line.startswith("--")):
                        continue
                    buffer.append(line)
                    if line.rstrip().endswith(";"):
                        cur.execute("".join(buffer))
                        buffer = []
                        executed += 1
                        if executed % 50 == 0:
                            logger.info("Executed {} statements", executed)
        raw.commit()
        logger.success("Loaded {} ({} statements)", path.name, executed)
    except Exception as exc:
        raw.rollback()
        logger.error("Load failed: {}", exc)
        sys.exit(1)
    finally:
        raw.close()


if __name__ == "__main__":
    main()
