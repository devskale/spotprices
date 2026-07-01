"""Webdummy site — a tiny FastAPI app mimicking Austrian electricity-provider
websites, so the tariff crawler (get_tarife.py) can be tested offline and
deterministically.

The provider list is fetched from the REAL Google Sheet (TARIF_CONFIG in
config.py) at startup, so the webdummy index always mirrors reality. Each
provider is served from a fixture HTML file in fixtures/<slug>.html; if no
fixture exists, a generated placeholder page is served instead (so nothing
404s and the crawler can still be exercised end-to-end).

Run interactively:
    uv run --group dev uvicorn tests.webdummy.server:app --port 8899 --reload

Then point the crawler at it:
    uv run python get_tarife.py \\
        --crawler direct \\
        --csv-url http://localhost:8899/tarife.csv \\
        --crawl-dir data/crawls_webdummy
"""
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
import uvicorn

from get_tarife import fetch_and_convert_csv_to_dict

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

app = FastAPI(title="Spotprices Webdummy", docs_url="/docs")


def _slugify(name: str) -> str:
    """Turn a provider name into a URL-safe slug used as fixture filename
    and route path. e.g. 'EnergieBurgenland' -> 'energieburgenland',
    'eSteiermark' -> 'esteiermark'."""
    return re.sub(r'[^a-z0-9]+', '', name.lower())


def _fixture(name: str) -> str | None:
    """Return fixture HTML for a slug, or None if no fixture file exists."""
    path = FIXTURES_DIR / f"{name}.html"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def _placeholder(name: str, provider: str, tarif_type: str) -> str:
    """Generate a minimal placeholder page for providers without a fixture.
    Includes a recognizable price so the crawler/LLM pipeline has something
    to extract."""
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>{provider} (placeholder)</title></head>
<body>
<nav>Home | Produkte | Kontakt</nav>
<header><h1>{provider} Stromtarife</h1></header>
<main>
<p>[webdummy placeholder for {provider} — no fixture file at fixtures/{name}.html]</p>
<h2>{provider} Beispiel Tarif</h2>
<ul>
    <li>Verbrauchspreis: 25,00 ct/kWh netto exkl. MWSt</li>
    <li>Vertragsbindung: 12 Monate</li>
    <li>Preisgarantie: 12 Monate</li>
    <li>Tarifart: {tarif_type}</li>
</ul>
</main>
<footer>© 2026 {provider} (webdummy placeholder)</footer>
</body></html>"""


# Fetch the real provider list from the Google Sheet at startup.
# Each entry: (slug, provider, tarif_type, real_url, has_fixture)
PROVIDERS: list[tuple[str, str, str, str, bool]] = []


def _load_providers() -> None:
    """Populate PROVIDERS from the real Google Sheet. Called at import time."""
    data = fetch_and_convert_csv_to_dict()
    for _desc, rows in data.items():
        for row in rows:
            provider = row.get("Anbieter", "unknown")
            tarif_type = row.get("Typ", "unknown")
            slug = _slugify(provider)
            real_url = row.get("Link", "")
            has_fixture = _fixture(slug) is not None
            # Deduplicate by provider name — a provider with multiple
            # rows only gets one route.
            if not any(p[0] == slug and p[1] == provider for p in PROVIDERS):
                PROVIDERS.append((slug, provider, tarif_type, real_url, has_fixture))


_load_providers()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """HTML index listing all real providers from the Google Sheet."""
    rows = []
    for slug, provider, typ, _real_url, has_fixture in PROVIDERS:
        tag = "fixture" if has_fixture else "placeholder"
        rows.append(
            f'<li><a href="/{slug}">{provider}</a> '
            f'<span class="type">({typ})</span> '
            f'<span class="tag">{tag}</span></li>'
        )
    n_fixture = sum(1 for p in PROVIDERS if p[4])
    n_total = len(PROVIDERS)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Webdummy</title>
<style>
body {{ font-family: sans-serif; max-width: 800px; margin: 2em auto; }}
li {{ margin: 4px 0; }}
.type {{ color: #6b7280; font-size: 0.9em; }}
.tag {{ font-size: 0.8em; padding: 1px 6px; border-radius: 3px;
       background: #e5e7eb; color: #374151; }}
</style></head>
<body>
<h1>Spotprices Webdummy</h1>
<p>Serving <strong>{n_total}</strong> providers from the real Google Sheet
({n_fixture} with fixtures, {n_total - n_fixture} placeholders).</p>
<ul>
{''.join(rows)}
</ul>
<p>Also: <a href="/tarife.csv">/tarife.csv</a> (crawler input)</p>
<p>Test routes:
   <a href="/delay/0">/delay/0</a>,
   <a href="/status/500">/status/500</a>
</p>
</body></html>"""


@app.get("/tarife.csv", response_class=PlainTextResponse)
def tarife_csv(request: Request) -> str:
    """CSV the crawler consumes. Columns match what get_tarife.crawl_data
    expects: Anbieter, Link, Typ, tool, crawl.

    URLs point back at this server (whatever host:port it's running on).
    All providers are marked crawl=y so the crawler fetches every one."""
    base = str(request.base_url).rstrip("/")
    lines = ["Anbieter,Link,Typ,tool,crawl"]
    for slug, provider, typ, _real_url, _has in PROVIDERS:
        lines.append(f"{provider},{base}/{slug},{typ},direct,y")
    return "\n".join(lines) + "\n"


@app.get("/delay/{seconds}", response_class=HTMLResponse)
def delay(seconds: float) -> str:
    """Sleeps then returns a normal page — for timeout-handling tests."""
    import time
    time.sleep(float(seconds))
    return _fixture("wienenergie") or ""


@app.get("/status/{code}")
def status(code: int) -> Response:
    """Returns the given HTTP status — for error-handling tests."""
    return Response(status_code=code, content=f"status {code}", media_type="text/plain")


# One route per provider slug. Registered dynamically after loading PROVIDERS.
def _make_provider_route(slug: str):
    def _route():
        html = _fixture(slug)
        if html is None:
            # Find this provider's info for the placeholder
            for s, provider, typ, _u, _f in PROVIDERS:
                if s == slug:
                    return HTMLResponse(_placeholder(slug, provider, typ))
        return HTMLResponse(html)
    _route.__name__ = f"provider_{slug}"
    return _route


# Register routes (dedupe by slug — a provider with multiple rows only needs
# one route).
_seen_slugs = set()
for _slug, _provider, _typ, _url, _has in PROVIDERS:
    if _slug not in _seen_slugs:
        app.add_api_route(f"/{_slug}", _make_provider_route(_slug),
                          response_class=HTMLResponse, methods=["GET"])
        _seen_slugs.add(_slug)


if __name__ == "__main__":
    uvicorn.run("tests.webdummy.server:app", host="127.0.0.1", port=8899, reload=True)
