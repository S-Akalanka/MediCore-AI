import datetime

from nawaloka.engine.prompt import format_schema

SCHEMA = {
    "admissions": {
        "columns": [{"name": "admission_id", "type": "INTEGER"}, {"name": "admission_date", "type": "DATE"}],
        "primary_key": ["admission_id"],
        "foreign_keys": [],
        "samples": [],
        "date_ranges": {"admission_date": (datetime.date(2022, 1, 1), datetime.date(2024, 12, 31))},
    }
}


def test_schema_text_includes_date_range_and_keys():
    text = format_schema(SCHEMA)
    assert "range admission_date: 2022-01-01 to 2024-12-31" in text
    assert "admission_id INTEGER PK" in text
