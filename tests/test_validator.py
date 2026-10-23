from nawaloka.engine.validator import validate_sql

SCHEMA = {
    "patients": {"columns": [{"name": "patient_id"}, {"name": "first_name"}]},
    "doctors": {"columns": [{"name": "doctor_id"}, {"name": "last_name"}]},
}


def test_select_is_allowed_and_limited():
    result = validate_sql("SELECT first_name FROM patients", SCHEMA)
    assert result.ok
    assert "LIMIT" in result.sql.upper()


def test_delete_is_blocked():
    result = validate_sql("DELETE FROM patients", SCHEMA)
    assert not result.ok and result.blocked


def test_drop_is_blocked():
    result = validate_sql("DROP TABLE patients", SCHEMA)
    assert not result.ok and result.blocked


def test_multiple_statements_are_blocked():
    result = validate_sql("SELECT 1; DELETE FROM patients", SCHEMA)
    assert result.blocked


def test_unknown_table_is_rejected():
    result = validate_sql("SELECT * FROM ghosts", SCHEMA)
    assert not result.ok and not result.blocked


def test_unknown_column_is_rejected():
    result = validate_sql("SELECT salary FROM patients", SCHEMA)
    assert not result.ok


def test_alias_in_order_by_is_allowed():
    result = validate_sql("SELECT first_name AS n FROM patients ORDER BY n", SCHEMA)
    assert result.ok


def test_dangerous_function_is_blocked():
    result = validate_sql("SELECT pg_sleep(10)", SCHEMA)
    assert result.blocked


def test_syntax_error_is_rejected():
    result = validate_sql("SELEC FROM", SCHEMA)
    assert not result.ok
