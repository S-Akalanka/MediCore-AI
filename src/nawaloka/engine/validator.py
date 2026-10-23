from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from nawaloka.config import SQL_ROW_LIMIT

BLOCKED_FUNCTIONS = {"pg_sleep", "pg_read_file", "pg_ls_dir", "set_config", "lo_import", "lo_export", "dblink"}


@dataclass
class ValidationResult:
    ok: bool
    sql: str = ""
    errors: list[str] = field(default_factory=list)
    blocked: bool = False


def validate_sql(sql: str, schema: dict) -> ValidationResult:
    """Check that SQL is a single safe SELECT that matches the schema."""
    try:
        statements = [s for s in sqlglot.parse(sql, dialect="postgres") if s is not None]
    except ParseError as exc:
        return ValidationResult(False, errors=[f"Syntax error: {exc}"])
    if len(statements) != 1:
        return ValidationResult(False, errors=["Exactly one statement is allowed"], blocked=True)
    tree = statements[0]

    if not isinstance(tree, (exp.Select, exp.SetOperation)):
        return ValidationResult(False, errors=["Only SELECT statements are allowed"], blocked=True)
    unsafe = (exp.DML, exp.DDL, exp.Command, exp.Into, exp.TruncateTable)
    if any(True for _ in tree.find_all(*unsafe)):
        return ValidationResult(False, errors=["Data modification is not allowed"], blocked=True)
    for func in tree.find_all(exp.Anonymous):
        if str(func.this).lower() in BLOCKED_FUNCTIONS:
            return ValidationResult(False, errors=[f"Function {func.this} is not allowed"], blocked=True)

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    known_tables = {name.lower() for name in schema}
    errors = []
    used_tables = set()
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name in cte_names:
            continue
        if name not in known_tables:
            errors.append(f"Unknown table: {table.name}")
        else:
            used_tables.add(name)

    known_columns = {c["name"].lower() for t in used_tables for c in schema[t]["columns"]}
    aliases = {a.alias.lower() for a in tree.find_all(exp.Alias)}
    aliases |= {a.alias.lower() for a in tree.find_all(exp.TableAlias)}
    for column in tree.find_all(exp.Column):
        name = column.name.lower()
        if name and name not in known_columns and name not in aliases and not isinstance(column.this, exp.Star):
            errors.append(f"Unknown column: {column.name}")

    if errors:
        return ValidationResult(False, errors=sorted(set(errors)))

    if isinstance(tree, exp.Select) and not tree.args.get("limit"):
        tree = tree.limit(SQL_ROW_LIMIT)
    return ValidationResult(True, sql=tree.sql(dialect="postgres"))
