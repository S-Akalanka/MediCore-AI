# MediCore AI

Ask questions about hospital data in plain English and get back results, charts and short insights, without writing SQL.

I built this to explore how far a small multi-agent pipeline can go on a realistic 12-table hospital database (about 50,000 patients and 200,000 appointments) while keeping generated SQL safe. A router, a SQL generator, a result interpreter and a fallback agent are wired together with LangGraph, and every step is traced.

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

Design notes, real query traces and a discussion of what I would change for production are in [report/design_notes.md](report/design_notes.md).

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

Example questions to try are in [sample_questions.md](sample_questions.md).

## Deployment

Pushes to `master` run the tests, build the image into GitHub Container Registry and deploy it to EC2 over SSH (`.github/workflows/deploy.yml`). The deploy needs the `EC2_HOST`, `EC2_USER` and `EC2_SSH_KEY` secrets in the GitHub `production` environment.

On the server the stack has three containers:

| Service | Role |
|---|---|
| app | Streamlit, only reachable inside the Docker network |
| nginx | Serves ports 80 and 443, redirects HTTP to HTTPS and proxies to the app |
| certbot | Renews the Let's Encrypt certificate every 12 hours |

The server keeps its own `.env`, which is never committed. Set `DOMAIN` there to a hostname that points at the server, for example `nawaloka.16.176.5.126.sslip.io`. The first deploy issues the certificate with `scripts/init_letsencrypt.sh`, and later deploys reuse it.

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
report/            design notes
tests/             unit tests
```
