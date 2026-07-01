# TODO / Known Issues

Project-level backlog and notes. Items here are not blocking but should be
addressed. Move items out as they are implemented.

## Crawler

### PDF crawling (Spotty, possibly others)

Spotty's tariffs are published as a PDF (`https://www.spottyenergie.at/agb`,
currently `crawl=n` in the Google Sheet). The current crawler
(`get_tarife.py`) only handles HTML pages via the configured crawlers
(`w3m`/`jina`/`chawan`/`markdowner`/`direct`). A PDF extraction path would be
useful.

The `web_apis` server on amd already exposes `/pdf/to_md` (PDF→Markdown via
Bearer auth, see `livesystem.md`). Options:

1. **Reuse `/pdf/to_md`** — add a `pdf` crawler mode in `config.py` that POSTs
   the PDF URL to `https://amd1.mooo.com/api/pdf/to_md` and stores the returned
   Markdown. Lowest effort, reuses existing infra.
2. **Native extraction** — add a `pypdf`/`pdfplumber`-based extractor as a new
   crawler mode. No external dependency, but another thing to maintain.

Approach (1) is preferred. Add a `pdf` entry to `CRAWL_CONFIG` and a branch in
`crawl_data()` analogous to the `direct` mode, then set `tool=pdf` and
`crawl=y` for the Spotty row in the Google Sheet.

Also check whether other providers publish tariffs as PDF (e.g. AGB
documents) — this may unlock more than just Spotty.

**DONE** — went with approach (2) (native `pypdf`) to avoid the amd1 auth
dependency. Added a `pdf` crawler mode that downloads the PDF and extracts text
page-by-page. To use: set `tool=pdf` and `crawl=y` for the Spotty row in the
Google Sheet.

Check whether other providers publish tariffs as PDF (e.g. AGB documents) —
this may unlock more than just Spotty. **(still open)**

## Testing

- Add automated crawler tests against `tests/webdummy/` (server + fixtures
  exist; tests not yet written). **DONE** — `tests/test_crawler.py` spins up
  the webdummy server per session and tests the full crawl loop.
- Add pure-function tests for `parse_markdown_table()` and
  `normalize_strompreis_to_netto_exkl_mwst()` in
  `electricity/api/v1/endpoints/tarifliste.py`. **DONE** —
  `tests/test_tarifliste_parser.py`.
- Add FastAPI endpoint tests with `TestClient` for `/tarifliste` and
  `/spotprices/chart/latest`. **DONE** — `tests/test_endpoints.py`.
- Add mocked-API tests for Awattar/SmartEnergy unit conversion
  (`marketprice/10`, `/1.2` MWSt) using `responses`. **DONE** —
  `tests/test_api_clients.py`.

## Code quality

- **API path mismatch**: `main.py` mounts router at `/api/v1`, but the
  WordPress plugin and `livesystem.md` expect `/electricity/...`. Align the
  prefix. **DONE** — mounted at `/electricity`.
- **Magic path depth**: `tarifliste.py` and `spotprices.py` use
  `Path(__file__).resolve().parents[4]` to find `data/`. Derive from
  `CONFIG['db_path']` or `main.py`'s location instead. **DONE** — uses
  `CONFIG['db_path']`.
- **SQLite WAL mode**: enable `PRAGMA journal_mode=WAL` for non-blocking
  reads during cron writes. **DONE** — `db/utils.get_engine()` enables WAL.
- **SmartEnergy client signature drift**: `fetch_day_prices()` takes no `day`
  arg, unlike Awattar's `fetch_day_prices(day)`. Align the interface or drop
  it. **DONE** — `fetch_day_prices(self, day=None)` now matches Awattar.
- **SVG generation via string concatenation** in `gen_chartsvg.py`: use
  `xml.etree.ElementTree` or `xml.sax.saxutils.escape` for safety. **DONE** —
  `xml.sax.saxutils.escape()` wraps all user-derived strings.
- **Chart readability when scaled down**: the spot-price SVG is generated at
  a fixed 800x400 viewBox. When embedded in a WordPress page and scaled down
  (e.g. on mobile or in a narrow column), the axis labels, price values, and
  day labels become hard to read. **DONE** — compact viewBox (500x340),
  non-scaling text via CSS variable + ResizeObserver, responsive label
  hiding, edge-aware min/max label placement, `showcase.py` viewer.
- **Unused deps**: `python-dotenv` (secrets come from `passwords.json`),
  `pandas` (only used by `print_chart.py` and `spot_price_analyzer.py`).
  Either use or remove. **DONE** — `python-dotenv` removed; `pandas` removed
  along with the unused `utils/spot_price_analyzer.py` and its test.

## Hygiene

- Move root-level debug scripts (`debug_file_processing.py`, `debug_llm.py`,
  `deploy_api_fix.sh`, `strom-tarif-pugin-test.html`) to `scripts/` or delete.
  **DONE** — moved to `scripts/`, deleted unused ones.
- `print_chart.py` uses `matplotlib` which is not in `pyproject.toml` deps —
  add it or remove the file. **DONE** — moved to `scripts/`, matplotlib added
  to dev deps.
- `description/` folder — review and archive or delete. **DONE** — moved to
  `docs/`.

## Security

- **WordPress password in git history**: `wp_postings.py` hardcoded a
  WordPress application password (commit `f68a708`). The code now reads from
  `passwords.json`, but **the old password must be rotated** in WP admin and
  the history scrubbed with `git filter-repo`. **DONE** — history scrubbed
  with `git filter-repo`, force-pushed to origin. (Password rotation in WP
  admin must still be done manually if not already.)
- Add a GitHub Action running `uv run --group dev ruff check .` + `pytest`.
  **DONE** — `.github/workflows/ci.yml`.
