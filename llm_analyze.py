import os
import time
import argparse
import re
from pathlib import Path

from config import LLM_CONFIG, QUERY_CONFIG

# uniinfer + credgoo provide direct LLM access without going through the
# amd1 proxy. Providers are resolved from the 'provider@model' strings in
# LLM_CONFIG; API keys are fetched via credgoo (falling back to env vars).
from uniinfer import ProviderFactory, ChatMessage, ChatCompletionRequest
from uniinfer.errors import UniInferError
from credgoo import get_api_key


# Cache provider instances so we don't re-fetch the API key on every call.
_PROVIDER_CACHE: dict[str, object] = {}


def extract_url_from_frontmatter(content):
    """Extract URL from YAML frontmatter at the beginning of content."""
    match = re.match(r'^---\s*\nurl:\s*(\S+)', content)
    if match:
        return match.group(1)
    match = re.search(r'^\s*URL:\s*(\S+)', content, flags=re.MULTILINE)
    if match:
        return match.group(1)
    return None


def _get_provider(provider_name: str):
    """Return a cached uniinfer provider instance, fetching its API key via
    credgoo (or env var). Returns None if the key can't be resolved."""
    if provider_name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider_name]

    # credgoo service name matches the provider name for most providers; the
    # TU provider fetches its own key internally, so no key needed.
    api_key = None
    if provider_name != 'tu':
        api_key = os.environ.get(provider_name.upper() + '_API_KEY') or get_api_key(provider_name)
        if not api_key:
            print(f"FAIL No API key for provider: {provider_name}")
            return None

    try:
        provider = ProviderFactory.get_provider(provider_name, api_key=api_key)
    except ValueError as e:
        print(f"FAIL Unknown provider '{provider_name}': {str(e)[:50]}")
        return None

    _PROVIDER_CACHE[provider_name] = provider
    return provider


def llm_analyze(llm_model_name, query_name, context=None):
    """Sends a query to a specified LLM model and returns the response.

    llm_model_name is a key in LLM_CONFIG whose MODEL value uses the
    'provider@model' format (e.g. 'mistral@mistral-small-latest')."""
    llm_config = LLM_CONFIG.get(llm_model_name)
    if not llm_config:
        print(f"FAIL No config for: {llm_model_name}")
        return None

    query_config = QUERY_CONFIG.get(query_name)
    if not query_config:
        print(f"FAIL No query: {query_name}")
        return None

    query = query_config[0].get("QUERY")
    if context:
        query = f"{query}\n\n{context}"

    # MODEL is 'provider@model_id' — uniinfer resolves the provider and credgoo
    # resolves the key.
    model_str = llm_config[0].get("MODEL")
    if '@' not in model_str:
        print(f"FAIL Model '{model_str}' must be 'provider@model_id'")
        return None
    provider_name, model_id = model_str.split('@', 1)

    provider = _get_provider(provider_name)
    if provider is None:
        return None

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=query)],
        model=model_id,
        max_tokens=4000,
        temperature=0.1,
    )

    try:
        response = provider.complete(request)
        return response.message.content
    except UniInferError as e:
        print(f"FAIL {llm_model_name}: {str(e)[:80]}")
        return None
    except Exception as e:
        print(f"FAIL {llm_model_name}: {str(e)[:80]}")
        return None


def llmanalyze_files(llm_model='tu@mistral', files='crawl_', query_to_use='TARIFLISTE_ABFRAGE', maxtokens=20000, max_files=None, max_retries=3):
    """Processes files and saves results to a report file."""
    flist = sorted([f for f in os.listdir('data/crawls') if files in f])
    if max_files:
        flist = flist[:max_files]

    if not flist:
        print("No files to analyze")
        return None

    print(f"Analyzing {len(flist)} files with {llm_model}...")

    report_path = f'data/crawls/report_{time.strftime("%Y%m%d")}.txt'
    success_count = 0
    fail_count = 0
    failed_files = []

    with open(report_path, 'a', encoding='utf-8') as report_file:
        for i, f in enumerate(flist, 1):
            content = Path(f'data/crawls/{f}').read_text(encoding='utf-8')
            tokens = len(content) // 4
            if tokens > maxtokens:
                content = content[:maxtokens * 4]

            provider = f.split('_')[1] if '_' in f else 'unknown'
            print(f"  [{i}/{len(flist)}] {provider} ({tokens}t)", end=" ", flush=True)

            # Retry logic with exponential backoff
            result = None
            for attempt in range(max_retries):
                result = llm_analyze(llm_model, query_to_use, context=content)
                if result:
                    break
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)  # 2, 4, 8 seconds
                    print(f"r{attempt+1}", end=" ", flush=True)
                    time.sleep(wait_time)

            if result:
                url = extract_url_from_frontmatter(content)
                url_line = f"URL: {url}\n" if url else ""
                report_file.write(f"-- Stromanbieter: {provider}\n{url_line}{result}\n\n")
                print("OK")
                success_count += 1
                time.sleep(2)
            else:
                print(f"FAIL (failed after {max_retries} attempts)")
                fail_count += 1
                failed_files.append(f)

    # Summary
    print(f"\n{'='*50}")
    print(f"Analysis complete: {success_count} OK, {fail_count} FAIL")
    if failed_files:
        print(f"Failed files: {', '.join(failed_files)}")
    print(f"{'='*50}")

    return report_path


def solidify_report(report_path, query_to_use='TARIF_TABELLE', llm_model='mistral@medium', ending='tab.md', maxtokens=30000):
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
            print(f"OK\n-> {out_path}")
            return out_path
        else:
            print("FAIL")
            return None
    except FileNotFoundError:
        print(f"FAIL Not found: {report_path}")
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
    parser.add_argument('--report-model', default='mistral@medium')
    args = parser.parse_args()

    from pathlib import Path

    report_path = None

    if args.step in ['files', 'both']:
        del_files(contains='report_', doesnotcontain='tab.md')
        report_path = llmanalyze_files(
            llm_model='mistral@small',
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
