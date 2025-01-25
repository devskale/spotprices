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
                    encoding = response.headers['Content-Type'].split('charset=')[-1].strip()
                    
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



def crawl_data(data, crawler='w3m', n=1, fetchinterval=20, verbose=True, savetofile=True):
    """Fetches and saves crawl data for the first n crawlable entries using specified crawler,
    checking file modification time for the fetch interval."""
    crawl_dir = Path("data/crawls")
    crawl_dir.mkdir(parents=True, exist_ok=True)

    crawler_config = CRAWL_CONFIG.get(crawler, [])
    if not crawler_config:
        print(f"No configuration found for crawler: {crawler}")
        return

    crawler_prefix = crawler_config[0].get('PREFIX', '')
    crawler_bearer = crawler_config[0].get('Bearer','')

    crawled_count = 0
    # Corrected logic to get data
    for description, rows in data.items():
      for entry in rows:
          #print(entry)
          if n > 0 and crawled_count >= n:
              break
          # Updated check
          if entry.get('crawl', False) == True or entry.get('crawl', False) == 'y':
              url = entry.get("Link")
              energieanbieter = entry.get("Anbieter", "unknown")
              tariftype = entry.get("Typ", "unknown")
              if url:
                  now = datetime.now()
                  base_filename = f"crawl_{energieanbieter}_{tariftype}"
                  
                  matching_files = list(crawl_dir.glob(f"{base_filename}*.txt"))
                  
                  
                  if matching_files:
                    # sort the files based on modification time, latest first
                    matching_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    filepath = matching_files[0]
                    
                    
                    timestamp_match = re.search(r'_(\d{8}_\d{6})\.txt$', filepath.name)
                    if timestamp_match:
                        file_timestamp_str = timestamp_match.group(1)
                        file_timestamp = datetime.strptime(file_timestamp_str, "%Y%m%d_%H%M%S")
                        time_diff = now - file_timestamp
                        print(f"  File exists: {filepath}")
                        print(f"    Last modified: {file_timestamp}")
                        print(f"    Time difference: {time_diff}")
                        if time_diff <= timedelta(seconds=fetchinterval):
                             print(f"  Skipping {url} due to fetch interval.")
                             continue
                         # we still need to add the timestamp
                        timestamp = now.strftime("%Y%m%d_%H%M%S")
                        filepath = crawl_dir / f"{base_filename}_{timestamp}.txt"
                    else:
                       print(f"  No timestamp found in filename {filepath.name}")
                       timestamp = now.strftime("%Y%m%d_%H%M%S")
                       filepath = crawl_dir / f"{base_filename}_{timestamp}.txt"

                  else:
                       print(f"  File does not exist: {filepath}")
                       timestamp = now.strftime("%Y%m%d_%H%M%S")
                       filepath = crawl_dir / f"{base_filename}_{timestamp}.txt"

                  try:
                        encoded_url = urllib.parse.quote_plus(url)
                        crawl_url = f"{crawler_prefix}{encoded_url}"
                        headers = {}
                        if crawler_bearer:
                            headers['Authorization'] = f'Bearer {crawler_bearer}'
                        
                        response = requests.get(crawl_url, headers=headers)
                        response.raise_for_status()

                           # Decode content based on Content-Type header or try utf-8 if header not found or if it does not define charset
                        if 'Content-Type' in response.headers and 'charset' in response.headers['Content-Type']:
                            encoding = response.headers['Content-Type'].split('charset=')[-1].strip()
                            
                        else:
                            encoding = 'utf-8'

                        if verbose:
                            print(f"Fetched data from {url}")
                        if savetofile:
                            with open(filepath, "w", encoding=encoding) as file:
                                file.write(response.text)
                            print(f"Successfully crawled and saved {filepath}")
                        crawled_count += 1

                  except requests.exceptions.RequestException as e:
                           print(f"Error fetching URL {url}: {e}")
                  except Exception as e:
                          print(f"An unexpected error occurred: {e}")    

if __name__ == "__main__":
    data = fetch_and_convert_csv_to_dict()
    #print(data)
    #print_data_beautifully(data)
    crawl_data(data=data, crawler='w3m', n=0, fetchinterval=20, verbose=True, savetofile=True)
