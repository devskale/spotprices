# AGENTS.md

Guidelines for AI agents (and humans) working in this repo.

## Tooling

- **Always use `uv`** for Python package management and running commands.
  - Install deps: `uv sync --group dev`
  - Run a tool: `uv run --group dev <tool>`
  - Install a Python tool: `uv tool install <pkg>` (not `pip install`)
  - Never use bare `pip`, `python`, or `pytest` — always go through `uv run`.
- Python 3.13+ is the target runtime.

## Common commands

```bash
# Install everything (main + dev deps)
uv sync --group dev

# Lint
uv run --group dev ruff check .

# Test (58 tests, ~75s — the crawler tests spin up the webdummy server)
uv run --group dev pytest

# Run the webdummy server (for interactive crawler testing)
uv run --group dev uvicorn tests.webdummy.server:app --port 8899 --reload

# Run the crawler against webdummy
uv run python get_tarife.py --crawler direct --csv-url http://localhost:8899/tarife.csv --crawl-dir data/crawls_webdummy

# Start the API server
uv run uvicorn main:app --reload
```

## Project layout

- `config.py` — central config (DB path, crawler/LLM config, `get_secret()`)
- `get_tarife.py` — tariff crawler (supports `direct`, `w3m`, `jina`, `chawan`, `markdowner`)
- `llm_analyze.py` — LLM tariff extraction via uniinfer + credgoo
- `gen_chartsvg.py` — spot-price SVG chart generation
- `db/` — SQLAlchemy models, operations, `get_engine()` (WAL mode)
- `api/` — Awattar + SmartEnergy price-API clients
- `electricity/` — FastAPI serving layer (`/electricity/tarifliste`, `/electricity/spotprices/...`)
- `strom-tarif-plugin/` — WordPress plugin (PHP)
- `tests/` — test suite + `webdummy/` mock provider server
- `scripts/` — debug/standalone scripts (not part of the app)
- `docs/` — documentation + `TODO.md` backlog

## Secrets

- Secrets live in `passwords.json` (gitignored) and are accessed via `get_secret()`.
- LLM API keys are resolved via credgoo (`get_api_key()`), not `passwords.json`.
- Never hardcode credentials. Never commit `passwords.json`.

## Testing

- Tests run offline. The crawler tests spin up `tests/webdummy/server.py` as a
  session-scoped fixture — no external network.
- Use `monkeypatch.setitem(CONFIG, key, value)` to patch the `CONFIG` dict
  (it's a plain dict, not an object — `monkeypatch.setattr` won't work).
- Module-level constants (e.g. `CHART_DIR`) need `monkeypatch.setattr(module, ...)`.
- The `db_session` fixture in `conftest.py` provides an in-memory SQLite session.

## Branches

- `main` — production
- `refactor/*` — work branches
