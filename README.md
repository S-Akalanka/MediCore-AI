# Nawaloka Hospital NL2SQL Platform

A multi-agent system that turns natural language questions into safe, validated SQL over the MediCore hospital database, then returns results, charts and plain English insights.

## Architecture

```mermaid
flowchart TD
    U[User question] --> H{History?}
    H -- yes --> C[Contextualizer]
    H -- no --> R
    C --> R[Intent Router]
    R -- destructive --> B[Blocked reply]
    R -- out of scope or unclear --> D[Direct reply]
    R -- data query --> G[SQL Generator]
    G --> V[Validator]
    V -- invalid --> G
    V -- valid --> E[Read-only Executor]
    E -- error --> G
    E -- rows --> I[Result Interpreter]
    G -- attempts exhausted --> F[Fallback]
    I --> O[Answer, chart, insight]
```

The full write-up, with query traces and a production readiness discussion, is in [report/engineering_report.md](report/engineering_report.md).

## Setup

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```
uv sync
copy .env.example .env
```

Fill in `.env`:

| Variable | Purpose |
|---|---|
| GROQ_API_KEY | LLM provider key |
| DATABASE_URL | Postgres connection string |
| LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL | Optional tracing |

Load the data and check the database:

```
uv run python scripts/load_dump.py path/to/medicore_data.sql
uv run python scripts/inspect_db.py
```

## Run

| Command | What it does |
|---|---|
| `uv run nawaloka` | Check configuration and environment |
| `uv run python scripts/ask.py "your question"` | Run the NL2SQL engine only |
| `uv run python scripts/run_pipeline.py` | Run 10 sample questions through all agents and write traces |
| `uv run streamlit run src/nawaloka/app.py` | Dashboard and Ask tabs |
| `uv run pytest -q` | Unit tests |

With Docker:

```
docker compose up --build
```

then open http://localhost:8501.

## Configuration

Settings live in `config/params.yaml` and model names in `config/models.yaml`. Secrets live only in `.env`.

## Safety

- The router stops requests to change data before any SQL is generated.
- Generated SQL is parsed with sqlglot. Only one SELECT is allowed, DML and DDL are blocked, unknown tables and columns are rejected, and a row limit is added.
- Queries run in a read-only transaction with a statement timeout.
- Users see friendly messages, never raw SQL errors.
- Use a read-only database role for `DATABASE_URL` in production.

## Project layout

```
config/            params.yaml, models.yaml
scripts/           database loading, inspection and run scripts
src/nawaloka/
  agents/          router, contextualizer, interpreter, fallback, orchestrator
  engine/          prompt builder, generator, validator, engine
  db/              engine, query runner, schema introspection
  dashboard/       panels, charts, service
  app.py           Streamlit UI
  observability.py LangFuse and token tracking
traces/            sample pipeline traces
report/            engineering report
tests/             unit tests
```
