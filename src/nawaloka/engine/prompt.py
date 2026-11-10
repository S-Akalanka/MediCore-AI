from datetime import date
from functools import lru_cache
from typing import Any

from nawaloka.db.schema import get_schema

SYSTEM_TEMPLATE = """You are a PostgreSQL expert for the MediCore Hospital CRM database.
Convert the user's question into one read-only SQL query.

Today's date is {today}. The data does not extend to today, so check the date ranges in the schema.

Database schema:
{schema}

Rules:
- Use only the tables and columns listed above.
- Output a single SELECT statement. Never modify data.
- Use explicit JOINs on the foreign keys shown.
- Add ORDER BY and LIMIT when the question asks for top or bottom results.
- Give columns readable aliases.
- Relative periods such as "last 6 months", "this year" or "recently" must be anchored to the latest date in the relevant table's range, not to today's date.
- In PostgreSQL, subtracting one date from another already returns an integer number of days. Do not wrap it in EXTRACT or EPOCH.
- For monthly or yearly series, group by DATE_TRUNC and keep a date value instead of formatting it as text, so results sort chronologically.
- For rates or percentages, compute a ratio (for example no-shows divided by total appointments), not a raw count.

Respond with JSON only:
{{"sql": "<query>", "clarification": ""}}
If the question is unrelated to the data, too vague, or cannot be answered from this schema, respond with:
{{"sql": "", "clarification": "<one short question or explanation for the user>"}}
"""


def _short(value: Any, limit: int = 40) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_schema(schema: dict[str, Any]) -> str:
    """Render the introspected schema as prompt text."""
    blocks = []
    for table, info in schema.items():
        lines = [f"Table {table}"]
        pk = set(info["primary_key"])
        for col in info["columns"]:
            tag = " PK" if col["name"] in pk else ""
            lines.append(f"  {col['name']} {col['type']}{tag}")
        for fk in info["foreign_keys"]:
            lines.append(
                f"  FK {', '.join(fk['columns'])} -> {fk['ref_table']}({', '.join(fk['ref_columns'])})"
            )
        for column, (low, high) in info.get("date_ranges", {}).items():
            lines.append(f"  range {column}: {low} to {high}")
        for sample in info["samples"]:
            lines.append("  sample: " + ", ".join(f"{k}={_short(v)}" for k, v in sample.items()))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


@lru_cache(maxsize=1)
def get_schema_data() -> dict[str, Any]:
    """Return the cached schema for the live database, shared by the prompt and the validator."""
    return get_schema(sample_rows=2, date_ranges=True)


@lru_cache(maxsize=1)
def get_schema_text() -> str:
    """Return the cached schema text for the live database."""
    return format_schema(get_schema_data())


def build_system_prompt() -> str:
    """Build the schema-aware system prompt."""
    return SYSTEM_TEMPLATE.format(today=date.today().isoformat(), schema=get_schema_text())
