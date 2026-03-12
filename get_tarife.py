import csv
import requests
from io import StringIO
from config import TARIF_CONFIG, CRAWL_CONFIG
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
import urllib.parse
import re
import argparse


def fetch_and_convert_csv_to_dict():
    """
    Fetches CSV data from the URL in config, parses it, and returns a dictionary.
    """
    all_data = {}
    for entry in TARIF_CONFIG['Tarifueberblick']:
        url = entry.get("url")
        description = entry.get("Beschreibung", "no description")

        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()

                # Decode content based on Content-Type header or try utf-8 if header not found or if it does not define charset
                if 'Content-Type' in response.headers and 'charset' in response.headers['Content-Type']:
                    encoding = response.headers['Content-Type'].split(
                        'charset=')[-1].strip()

                else:
                    encoding = 'utf-8'

                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)
                all_data[description] = list(reader)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching URL {url}: {e}")
            except csv.Error as e:
                print(f"Error parsing CSV data from {url}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        else:
            print(f"Skipping entry without a URL: {entry}")

    return all_data


def print_data_beautifully(data):
    """Prints the fetched data in a human-readable format."""
    if not data:
        print("No data to display.")
        return

    for description, rows in data.items():
        print(f"Data for: {description}\n")
        if not rows:
            print("No data rows available.\n")
        else:
            for row in rows:
                print(json.dumps(row, indent=4))
                print("----")


def crawl_data(data, default_crawler='w3m', n=1, fetchinterval=20, verbose=True, savetofile=True, anbieter=None):
    """Fetches and saves crawl data for the first n crawlable entries using specified crawler,
    appending multiple URLs to the same file for each provider."""
    crawl_dir = Path("data/crawls")
    crawl_dir.mkdir(parents=True, exist_ok=True)

    crawled_count = 0
    last_crawl_time = None  # Initialize variable to track last crawl time

    for description, rows in data.items():
        for entry in rows:
            if n > 0 and crawled_count >= n:
                break

            if anbieter and entry.get("Anbieter", "").lower() != anbieter.lower():
                continue

            if entry.get('crawl', False) == True or entry.get('crawl', False) == 'y':

                # Use 'tool' from data or default

                crawler = entry.get('tool', default_crawler)
                if crawler not in CRAWL_CONFIG:
                    crawler = default_crawler
                print(f"Crawling with {crawler}...")
                crawler_config = CRAWL_CONFIG.get(crawler, [])

                if not crawler_config:
                    print(f"No configuration found for crawler: {crawler}")
                    continue

                crawler_prefix = crawler_config[0].get('PREFIX', '')
                crawler_bearer = crawler_config[0].get('Bearer', '')

                url = entry.get("Link")
                energieanbieter = entry.get("Anbieter", "unknown")
                tariftype = entry.get("Typ", "unknown")
                if url:
                    now = datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    # Include a URL hash to differentiate multiple URLs from same provider
                    import hashlib
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
                    filepath = crawl_dir / f"crawl_{energieanbieter}_{tariftype}_{timestamp}_{url_hash}.txt"

                    # Check if file exists (unlikely with timestamp+hash)
                    if filepath.exists():
                        print(f"  File already exists: {filepath}")
                        continue
                    else:
                        print(f"  Creating: {filepath}")

                    try:
                        # Enforce wait time after last crawl
                        if last_crawl_time:
                            time_since_last_crawl = datetime.now() - last_crawl_time
                            if time_since_last_crawl < timedelta(seconds=2) and crawler != 'w3m':
                                wait_seconds = (
                                    timedelta(seconds=2) - time_since_last_crawl).total_seconds()
                                print(f"  Waiting {
                                      wait_seconds:.2f} seconds before next crawl...")
                                time.sleep(wait_seconds)

                        # Check if crawler uses local command (CMD) instead of web API (PREFIX)
                        crawler_cmd = crawler_config[0].get('CMD', '')
                        crawler_args = crawler_config[0].get('ARGS', '')
                        response_format = crawler_config[0].get('Format', 'txt')

                        if crawler_cmd:
                            # Use local command for crawling (e.g., chawan)
                            import subprocess
                            cmd = [crawler_cmd]
                            if crawler_args:
                                cmd.extend(crawler_args.split())
                            cmd.append(url)
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                            if result.returncode != 0:
                                print(f"Error running {crawler}: {result.stderr}")
                                continue
                            cleaned_text = result.stdout
                            encoding = 'utf-8'
                        else:
                            # Use web API for crawling
                            if crawler == 'jina':
                                crawl_url = f"{crawler_prefix}{url}"
                            else:
                                encoded_url = urllib.parse.quote_plus(url)
                                crawl_url = f"{crawler_prefix}{encoded_url}"
                            headers = {}
                            if crawler_bearer:
                                headers['Authorization'] = f'Bearer {
                                crawler_bearer}'

                            response = requests.get(crawl_url, headers=headers)
                            response.raise_for_status()

                            # Handle JSON response format (new amd1 API)
                            if response_format == 'json':
                                cleaned_text = response.json().get('content', '')
                                encoding = 'utf-8'
                            else:
                                # Decode content based on Content-Type header or try utf-8 if header not found
                                if 'Content-Type' in response.headers and 'charset' in response.headers['Content-Type']:
                                    encoding = response.headers['Content-Type'].split(
                                        'charset=')[-1].strip()
                                else:
                                    encoding = 'utf-8'
                                cleaned_text = response.text
                        # add energieanbieter to response text
                        cleaned_text = f"Energieanbieter: {
                            energieanbieter}\n{cleaned_text}"

                        # ADD CLEANUP HERE
                        # Remove unwanted characters.
                        # remove multiple line breaks
                        cleaned_text = re.sub(r'[\r\n]+', '\n', cleaned_text)
                        # remove multiple spaces
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                        # remove multiple --
                        cleaned_text = re.sub(r'-+', ' ', cleaned_text)
                        # remove &nbsp; (non-breaking space)
                        cleaned_text = re.sub(r'[\xa0]', ' ', cleaned_text)
                        # remove □
                        cleaned_text = re.sub(r'□', '', cleaned_text)
                        # remove multiple number of ━
                        cleaned_text = re.sub(r'━{2,}', '━', cleaned_text)

                        if verbose:
                            print(f"Fetched data from {url}")
                        if savetofile:
                            with open(filepath, "w", encoding=encoding) as file:
                                file.write(cleaned_text)
                            print(f"Successfully crawled and saved {filepath}")

                        crawled_count += 1
                        last_crawl_time = datetime.now()  # Update last crawl time

                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching URL {url}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")


def cleanup(n=1):
    """Keeps the n last versions of each crawl file per URL, deletes older versions."""
    crawl_dir = Path("data/crawls")
    if not crawl_dir.exists():
        print("No crawl directory found.")
        return

    files_by_base = {}
    for filepath in crawl_dir.glob("crawl_*.txt"):
        # Extract base filename including URL hash to group by unique URL
        # Format: crawl_Provider_Type_YYYYMMDD_HHMMSS_hash.txt
        match = re.match(
            r'(crawl_[^_]+_[^_]+)_\d{8}_\d{6}(_[a-f0-9]{6})?\.txt', filepath.name)
        if match:
            # Include hash in base if present (different URLs)
            url_hash = match.group(2) or ''
            base_filename = match.group(1) + url_hash
            if base_filename not in files_by_base:
                files_by_base[base_filename] = []
            files_by_base[base_filename].append(filepath)

    for base_filename, filepaths in files_by_base.items():
        if len(filepaths) > n:
            filepaths.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            files_to_delete = filepaths[n:]
            # print(f"  Found {len(files_to_delete)} old files for {base_filename}")
            for file_to_delete in files_to_delete:
                print(f"  (-) {file_to_delete}")
                os.remove(file_to_delete)
        else:
            # print(f"  No old files to delete for {base_filename}")
            print(".", end="")
    print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl tariff data for energy providers.")
    parser.add_argument('--anbieter', type=str, help="Filter by specific provider (Anbieter)")
    parser.add_argument('--crawler', type=str, default='w3m', help="Specify the crawler tool (default: w3m)")
    args = parser.parse_args()

    data = fetch_and_convert_csv_to_dict()
    # print(data)
    # print_data_beautifully(data)
    crawl_data(data=data, default_crawler=args.crawler, n=0,
               fetchinterval=20, verbose=True, savetofile=True, anbieter=args.anbieter)
    cleanup(n=1)
