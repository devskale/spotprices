import requests
from config import LLM_CONFIG, QUERY_CONFIG, PASSWORDS
import os
import time
import argparse
import re
from pathlib import Path


def extract_url_from_frontmatter(content):
    """Extract URL from YAML frontmatter at the beginning of content."""
    match = re.match(r'^---\s*\nurl:\s*(\S+)', content)
    if match:
        return match.group(1)
    match = re.search(r'^\s*URL:\s*(\S+)', content, flags=re.MULTILINE)
    if match:
        return match.group(1)
    return None


def llm_analyze(llm_model_name, query_name, context=None):
    """Sends a query to a specified LLM model and returns the response."""
    llm_config = LLM_CONFIG.get(llm_model_name)
    if not llm_config:
        print(f"✗ No config for: {llm_model_name}")
        return None

    query_config = QUERY_CONFIG.get(query_name)
    if not query_config:
        print(f"✗ No query: {query_name}")
        return None

    query = query_config[0].get("QUERY")
    if context:
        query = f"{query}\n\n{context}"

    base_url = llm_config[0].get("BASEURL")
    api_key = PASSWORDS.get(llm_config[0].get("APIKEY"))
    model = llm_config[0].get("MODEL")

    if not api_key:
        print(f"✗ No API key for: {llm_model_name}")
        return None

    headers = {"Content-Type": "application/json"}

    if 'openrouter' in llm_model_name or 'groq' in llm_model_name:
        headers['Authorization'] = f'Bearer {api_key}'
        data = {"model": model, "messages": [{"role": "user", "content": query}], "max_tokens": 4000, "temperature": 0.1}
    elif 'amp1' in llm_model_name:
        data = {"prompt": query, "model": model, "max_tokens": 4000}
    else:
        headers['Authorization'] = f'Bearer {api_key}'
        data = {"model": model, "messages": [{"role": "user", "content": query}], "max_tokens": 4000, "temperature": 0.1}

    try:
        endpoint = "/v1/completions" if 'amp1' in llm_model_name else "/chat/completions"
        response = requests.post(f"{base_url}{endpoint}", headers=headers, json=data, timeout=300)
        response.raise_for_status()

        if 'amp1' in llm_model_name:
            return response.json()['choices'][0]['text']
        return response.json()['choices'][0]['message']['content']

    except requests.exceptions.Timeout:
        print(f"✗ Timeout: {llm_model_name}")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return None


def llmanalyze_files(llm_model='tu@mistral', files='crawl_', query_to_use='TARIFLISTE_ABFRAGE', maxtokens=20000, max_files=None):
    """Processes files and saves results to a report file."""
    flist = sorted([f for f in os.listdir('data/crawls') if files in f])
    if max_files:
        flist = flist[:max_files]

    if not flist:
        print("No files to analyze")
        return None

    print(f"Analyzing {len(flist)} files with {llm_model}...")

    report_path = f'data/crawls/report_{time.strftime("%Y%m%d")}.txt'
    with open(report_path, 'a', encoding='utf-8') as report_file:
        for i, f in enumerate(flist, 1):
            content = Path(f'data/crawls/{f}').read_text(encoding='utf-8')
            tokens = len(content) // 4
            if tokens > maxtokens:
                content = content[:maxtokens * 4]

            provider = f.split('_')[1] if '_' in f else 'unknown'
            print(f"  [{i}/{len(flist)}] {provider} ({tokens}t)", end=" ", flush=True)

            result = llm_analyze(llm_model, query_to_use, context=content)

            if result:
                url = extract_url_from_frontmatter(content)
                url_line = f"URL: {url}\n" if url else ""
                report_file.write(f"-- Stromanbieter: {provider}\n{url_line}{result}\n\n")
                print("✓")
                time.sleep(2)
            else:
                print("✗")
                break

    return report_path


def solidify_report(report_path, query_to_use='TARIF_TABELLE', llm_model='groq@kimi', ending='tab.md', maxtokens=30000):
    """Reads report file and generates consolidated table."""
    try:
        content = Path(report_path).read_text(encoding='utf-8')
        tokens = len(content) // 4
        if tokens > maxtokens:
            content = content[:maxtokens * 4]

        print(f"Generating table with {llm_model} ({tokens}t)...", end=" ", flush=True)
        result = llm_analyze(llm_model, query_to_use, context=content)

        if result:
            out_path = f'{os.path.splitext(report_path)[0]}_{ending}'
            Path(out_path).write_text(result, encoding='utf-8')
            print(f"✓\n→ {out_path}")
            return out_path
        else:
            print("✗")
            return None
    except FileNotFoundError:
        print(f"✗ Not found: {report_path}")
        return None


def del_files(contains='report_', doesnotcontain=''):
    for f in os.listdir('data/crawls'):
        if contains in f and (not doesnotcontain or doesnotcontain not in f):
            try:
                os.remove(os.path.join('data/crawls', f))
            except OSError:
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze crawled files")
    parser.add_argument('--step', choices=['files', 'report', 'both'], default='both')
    parser.add_argument('--files', default='crawl_', help="File pattern (default: crawl_)")
    parser.add_argument('--max-files', type=int, default=None)
    parser.add_argument('--report-file', default=None)
    parser.add_argument('--report-model', default='groq@kimi')
    args = parser.parse_args()

    from pathlib import Path

    report_path = None

    if args.step in ['files', 'both']:
        del_files(contains='report_', doesnotcontain='tab.md')
        report_path = llmanalyze_files(
            llm_model='tu@mistral',
            files=args.files,
            query_to_use='TARIFLISTE_ABFRAGE',
            maxtokens=20000,
            max_files=args.max_files)

    if args.step in ['report', 'both']:
        if not report_path:
            report_path = args.report_file or f'data/crawls/report_{time.strftime("%Y%m%d")}.txt'
        solidify_report(
            report_path=report_path,
            query_to_use='TARIF_TABELLE',
            llm_model=args.report_model,
            ending='tab.md')
