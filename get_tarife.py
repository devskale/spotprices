import csv
import requests
from io import StringIO
from config import CRAWL_CONFIG, TARIF_CONFIG, get_secret
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import time
import urllib.parse
import re
import argparse
import subprocess


def fetch_and_convert_csv_to_dict():
    """Fetches CSV data from the URL in config, parses it, and returns a dictionary."""
    all_data = {}
    for entry in TARIF_CONFIG['Tarifueberblick']:
        url = entry.get("url")
        description = entry.get("Beschreibung", "no description")
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()
                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)
                all_data[description] = list(reader)
            except Exception as e:
                print(f"✗ CSV fetch error: {e}")
    return all_data


def crawl_data(data, default_crawler='w3m', n=0, anbieter=None):
    """Fetches and saves crawl data using specified crawler."""
    crawl_dir = Path("data/crawls")
    crawl_dir.mkdir(parents=True, exist_ok=True)

    crawled_count = 0
    last_crawl_time = None

    for description, rows in data.items():
        for entry in rows:
            if n > 0 and crawled_count >= n:
                break
            if anbieter and entry.get("Anbieter", "").lower() != anbieter.lower():
                continue

            crawl_flag = entry.get("crawl", False)
            if not (crawl_flag is True or str(crawl_flag).lower() == 'y'):
                continue

            crawler = entry.get('tool', default_crawler)
            if crawler not in CRAWL_CONFIG:
                crawler = default_crawler
            crawler_config = CRAWL_CONFIG.get(crawler, [])
            if not crawler_config:
                print(f"✗ No config for: {crawler}")
                continue

            crawler_prefix = crawler_config[0].get('PREFIX', '')
            crawler_bearer = crawler_config[0].get('Bearer', '')
            bearer_key = crawler_config[0].get("BearerKey", "")
            if bearer_key and not crawler_bearer:
                crawler_bearer = get_secret(bearer_key, "")

            url = entry.get("Link")
            provider = entry.get("Anbieter", "unknown")
            tarif_type = entry.get("Typ", "unknown")

            if not url:
                continue

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
            filepath = crawl_dir / f"crawl_{provider}_{tarif_type}_{timestamp}_{url_hash}.txt"

            if filepath.exists():
                print(f"⏭ {provider}/{tarif_type}")
                continue

            try:
                # Rate limiting for non-w3m crawlers
                if last_crawl_time and crawler != 'w3m':
                    elapsed = datetime.now() - last_crawl_time
                    if elapsed < timedelta(seconds=2):
                        time.sleep((timedelta(seconds=2) - elapsed).total_seconds())

                crawler_cmd = crawler_config[0].get('CMD', '')
                crawler_args = crawler_config[0].get('ARGS', '')
                response_format = crawler_config[0].get('Format', 'txt')

                if crawler_cmd:
                    cmd = [crawler_cmd]
                    if crawler_args:
                        cmd.extend(crawler_args.split())
                    cmd.append(url)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode != 0:
                        print(f"✗ {crawler} failed")
                        continue
                    text = result.stdout
                else:
                    if crawler == 'jina':
                        crawl_url = f"{crawler_prefix}{url}"
                    else:
                        crawl_url = f"{crawler_prefix}{urllib.parse.quote_plus(url)}"
                    headers = {"Authorization": f"Bearer {crawler_bearer}"} if crawler_bearer else {}
                    response = requests.get(crawl_url, headers=headers)
                    response.raise_for_status()
                    text = response.json().get('content', '') if response_format == 'json' else response.text

                # Clean text
                text = f"Energieanbieter: {provider}\n{text}"
                text = re.sub(r'[\r\n]+', '\n', text)
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'-+', ' ', text)
                text = re.sub(r'[\xa0□]', ' ', text)
                text = re.sub(r'━{2,}', '━', text)

                # Add frontmatter
                crawl_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                text = f"---\nurl: {url}\ncrawl_date: {crawl_date}\nprovider: {provider}\ntype: {tarif_type}\n---\n\n{text}"

                filepath.write_text(text, encoding='utf-8')
                print(f"✓ {provider}/{tarif_type} [{crawler}]")
                crawled_count += 1
                last_crawl_time = datetime.now()

            except Exception as e:
                print(f"✗ {url[:40]}: {str(e)[:50]}")

    print(f"\nCrawled: {crawled_count}")


def cleanup(n=1):
    """Keeps the n last versions of each crawl file per URL."""
    crawl_dir = Path("data/crawls")
    if not crawl_dir.exists():
        return

    files_by_base = {}
    for filepath in crawl_dir.glob("crawl_*.txt"):
        match = re.match(r'(crawl_[^_]+_[^_]+)_\d{8}_\d{6}(_[a-f0-9]{6})?\.txt', filepath.name)
        if match:
            base = match.group(1) + (match.group(2) or '')
            files_by_base.setdefault(base, []).append(filepath)

    deleted = 0
    for filepaths in files_by_base.values():
        if len(filepaths) > n:
            for f in sorted(filepaths, key=lambda x: x.stat().st_mtime, reverse=True)[n:]:
                f.unlink()
                deleted += 1

    if deleted:
        print(f"Cleaned: {deleted} old files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl tariff data")
    parser.add_argument('--anbieter', type=str, help="Filter by provider")
    parser.add_argument('--crawler', type=str, default='w3m', help="Crawler tool (default: w3m)")
    args = parser.parse_args()

    data = fetch_and_convert_csv_to_dict()
    crawl_data(data=data, default_crawler=args.crawler, n=0, anbieter=args.anbieter)
    cleanup(n=1)
