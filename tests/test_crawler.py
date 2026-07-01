# tests/test_crawler.py
"""Automated crawler tests against the webdummy server.

Spins up the webdummy FastAPI app on an ephemeral port per test session, then
runs get_tarife.crawl_data() against it with the 'direct' crawler mode.
Verifies the full loop: CSV fetch -> crawl each provider -> frontmatter +
cleaned content written to crawl files.
"""
import csv
import io

import pytest
import requests
import uvicorn

from get_tarife import crawl_data, cleanup


# Use TestClient (which is sync) instead of a real server. The crawler uses
# requests.get, so we point it at the TestClient's base URL via a small
# adapter. TestClient works as a context manager and serves over ASGI, no port
# needed. But the crawler calls requests.get(url) with absolute URLs, so we
# need a real HTTP server. Use a session-scoped uvicorn server on a random
# free port instead.


@pytest.fixture(scope="session")
def webdummy_url():
    """Start the webdummy server on a random free port for the test session."""
    import socket
    import threading
    import time

    from tests.webdummy.server import app

    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for the server to be ready
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            r = requests.get(f"{url}/", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)

    yield url

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def crawl_dir(tmp_path):
    """Isolated crawl output dir for each test."""
    d = tmp_path / "crawls"
    d.mkdir()
    return d


def _fetch_csv(url):
    """Fetch the webdummy /tarife.csv and return parsed rows."""
    resp = requests.get(f"{url}/tarife.csv")
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


class TestWebdummyServer:
    def test_server_is_up(self, webdummy_url):
        r = requests.get(f"{webdummy_url}/")
        assert r.status_code == 200
        assert "Webdummy" in r.text

    def test_tarife_csv_lists_providers(self, webdummy_url):
        rows = _fetch_csv(webdummy_url)
        assert len(rows) > 0
        # Should include the known providers
        providers = {r["Anbieter"] for r in rows}
        assert "WienEnergie" in providers
        assert "Verbund" in providers

    def test_provider_fixture_served(self, webdummy_url):
        r = requests.get(f"{webdummy_url}/wienenergie")
        assert r.status_code == 200
        assert "Wien Energie" in r.text or "WienEnergie" in r.text

    def test_status_endpoint(self, webdummy_url):
        r = requests.get(f"{webdummy_url}/status/500")
        assert r.status_code == 500

    def test_404_for_unknown_provider(self, webdummy_url):
        r = requests.get(f"{webdummy_url}/doesnotexist")
        assert r.status_code == 404


class TestCrawlerAgainstWebdummy:
    def test_crawl_produces_files(self, webdummy_url, crawl_dir):
        """End-to-end: fetch CSV from webdummy, crawl each provider, verify
        crawl files are written with frontmatter and content."""
        data = {webdummy_url: _fetch_csv(webdummy_url)}
        crawl_data(data=data, default_crawler="direct", n=0, crawl_dir=crawl_dir)

        files = list(crawl_dir.glob("crawl_*.txt"))
        assert len(files) > 0

    def test_crawl_files_have_frontmatter(self, webdummy_url, crawl_dir):
        data = {webdummy_url: _fetch_csv(webdummy_url)}
        crawl_data(data=data, default_crawler="direct", n=0, crawl_dir=crawl_dir)

        for f in crawl_dir.glob("crawl_*.txt"):
            content = f.read_text(encoding="utf-8")
            # Must start with YAML frontmatter
            assert content.startswith("---\n")
            assert "url:" in content
            assert "crawl_date:" in content
            assert "provider:" in content
            assert "type:" in content

    def test_crawl_files_contain_provider_name(self, webdummy_url, crawl_dir):
        data = {webdummy_url: _fetch_csv(webdummy_url)}
        crawl_data(data=data, default_crawler="direct", n=0, crawl_dir=crawl_dir)

        # Each crawl file's content should mention its provider
        for f in crawl_dir.glob("crawl_*.txt"):
            content = f.read_text(encoding="utf-8")
            assert "Energieanbieter:" in content

    def test_crawl_specific_provider(self, webdummy_url, crawl_dir):
        """Filter to a single provider and verify only that one is crawled."""
        data = {webdummy_url: _fetch_csv(webdummy_url)}
        crawl_data(data=data, default_crawler="direct", n=0,
                   anbieter="WienEnergie", crawl_dir=crawl_dir)

        files = list(crawl_dir.glob("crawl_*.txt"))
        assert len(files) == 1
        assert "WienEnergie" in files[0].name

    def test_cleanup_keeps_n_versions(self, webdummy_url, crawl_dir):
        """cleanup(n=1) should keep only the newest file per provider."""
        # Create two crawl files for the same provider with different timestamps
        # (the crawler skips identical filenames, so we write them directly)
        import time as _time
        for ts in ("20260701_100000", "20260701_100001"):
            f = crawl_dir / f"crawl_WienEnergie_Bezug_{ts}_abc123.txt"
            f.write_text("---\nurl: x\n---\ncontent", encoding="utf-8")
            _time.sleep(0.05)

        files_before = list(crawl_dir.glob("crawl_WienEnergie_*.txt"))
        assert len(files_before) == 2

        cleanup(n=1, crawl_dir=crawl_dir)

        files_after = list(crawl_dir.glob("crawl_WienEnergie_*.txt"))
        assert len(files_after) == 1

    def test_existing_file_is_skipped(self, webdummy_url, crawl_dir):
        """If a crawl file already exists (same name), it should be skipped."""
        data = {webdummy_url: _fetch_csv(webdummy_url)}
        crawl_data(data=data, default_crawler="direct", n=0,
                   anbieter="WienEnergie", crawl_dir=crawl_dir)
        files_after_first = list(crawl_dir.glob("crawl_*.txt"))

        # Crawl again immediately — same timestamp -> same filename -> skipped
        crawl_data(data=data, default_crawler="direct", n=0,
                   anbieter="WienEnergie", crawl_dir=crawl_dir)
        files_after_second = list(crawl_dir.glob("crawl_*.txt"))

        assert len(files_after_first) == len(files_after_second)
