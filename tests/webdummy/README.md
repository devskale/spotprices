# Webdummy site

A tiny FastAPI app that mimics Austrian electricity-provider websites, so the
tariff crawler (`get_tarife.py`) can be tested end-to-end **offline and
deterministically** — no real provider sites, no jina/w3m/markdowner services,
no flaky network.

## Run it

```bash
uv run --group dev uvicorn tests.webdummy.server:app --port 8765 --reload
```

Then open http://localhost:8765/ in a browser to see the index of served
fixtures.

## What it serves

| Route | Content |
|-------|---------|
| `/` | HTML index listing all fixtures |
| `/tarife.csv` | CSV the crawler consumes (Anbieter, Link, Typ, tool, crawl columns) |
| `/wienenergie` | Wien Energie tariff page fixture |
| `/verbund` | Verbund tariff page fixture |
| `/oemag` | OEMAG tariff page fixture |
| `/energieburgenland` | Energie Burgenland fixture |
| `/awattar` | Awattar dynamic-pricing fixture |
| `/smartenergy` | SmartEnergy fixture |
| `/oekostrom` | Oekostrom fixture |
| `/malformed` | Deliberately broken page (missing prices) for parser-robustness tests |
| `/delay/<n>` | Page that sleeps `n` seconds — for timeout testing |
| `/status/<code>` | Returns the given HTTP status — for error-handling tests |

All HTML fixtures live in `fixtures/*.html` and can be edited freely to test
new parser/LLM-extraction scenarios.

## Point the crawler at it

```bash
uv run python get_tarife.py \
  --crawler direct \
  --csv-url http://localhost:8765/tarife.csv \
  --crawl-dir data/crawls_webdummy
```

The `direct` crawler (defined in `config.py`) fetches each URL straight from
the webdummy server instead of going through jina/w3m/markdowner.

## Run it from tests

`server.py` also exposes a pytest fixture via `conftest.py` (TODO) so tests can
spin it up on a random port per session. For now, run it manually and test
interactively.
