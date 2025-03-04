import requests
import json
from config import LLM_CONFIG, QUERY_CONFIG, PASSWORDS
import os
import time


def llm_analyze(llm_model_name, query_name, context=None):
    """
    Sends a query to a specified LLM model and returns the response.

    Args:
        llm_model_name (str): The name of the LLM model to use (e.g., 'amp1', 'openrouter_llama3.3:70b').
        query_name (str): The name of the query to use (e.g., 'BEZUGSPREIS_ABFRAGE').
        context (str, optional): An optional context string to add to the query. Defaults to None.

    Returns:
        str: The response from the LLM model, or None if an error occurs.
    """

    llm_config = LLM_CONFIG.get(llm_model_name)
    if not llm_config:
        print(f"Error: No configuration found for LLM model: {llm_model_name}")
        return None

    query_config = QUERY_CONFIG.get(query_name)
    if not query_config:
        print(f"Error: No query found for query name: {query_name}")
        return None

    query = query_config[0].get("QUERY")

    # Add context to the query if provided
    if context:
        query = f"{query}\n\n{context}"

    base_url = llm_config[0].get("BASEURL")
    api_key_handle = llm_config[0].get("APIKEY")
    api_key = PASSWORDS.get(api_key_handle)
    if not api_key:
        print(f"Error: No API key found for {api_key_handle}")
        return None
    model = llm_config[0].get("MODEL")

    headers = {
        "Content-Type": "application/json"
    }

    if 'openrouter' in llm_model_name:
        headers['Authorization'] = f'Bearer {api_key}'
        data = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }

    elif 'amp1' in llm_model_name:
        data = {
            "prompt": query,
            "model": model
        }
    else:  # openai fallback
        headers['Authorization'] = f'Bearer {api_key}'
        data = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }

    try:
        if 'openrouter' in llm_model_name:
            response = requests.post(
                f"{base_url}/chat/completions", headers=headers, json=data)
        elif 'amp1' in llm_model_name:
            response = requests.post(
                f"{base_url}/v1/completions", headers=headers, json=data)
        else:
            response = requests.post(
                f"{base_url}/chat/completions", headers=headers, json=data)

        response.raise_for_status()  # Raise an exception for bad status codes

        if 'openrouter' in llm_model_name:
            return response.json()['choices'][0]['message']['content']
        elif 'amp1' in llm_model_name:
            return response.json()['choices'][0]['text']
        else:
            return response.json()['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        print(f"Error during request to {llm_model_name}: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing response from {llm_model_name}: {e}")
        print(response.text)
        return None


def llmanalyze_files(llm_model='arli_nemo', files='crawl_', query_to_use='TARIFLISTE_ABFRAGE', maxtokens=12000):
    """
    Processes files in the 'data/crawls' directory, sends them to the LLM for analysis,
    and saves the results to a report file.

    Args:
        llm_model (str): The name of the LLM model to use.
        query_to_use (str): The name of the query to use.
        maxtokens (int, optional): The maximum number of tokens to use from a file. Defaults to 12000.
    """
    flist = [f for f in os.listdir('data/crawls') if files in f]
    print(flist)

    # Create or open the report file
    report_file_path = f'data/crawls/report_{time.strftime("%Y%m%d")}.txt'
    with open(report_file_path, 'a', encoding='utf-8') as report_file:
        # Loop through the file list
        for f in flist:
            with open(f'data/crawls/{f}', 'r', encoding='utf-8') as file:
                example_context = file.read()
                tokens = round(len(example_context) / 4)
                if tokens > maxtokens:
                    print(f"Context is too long ({tokens} tokens). Truncated at {
                          maxtokens} tokens.")
                    example_context = example_context[:maxtokens * 4]

                print(f' {llm_model} ({flist.index(f) + 1}/{len(flist)
                                                            }) analyzing {f} / {tokens} tokens')

                result = llm_analyze(
                    llm_model, query_to_use, context=example_context)

                if result:
                    # Print response in light grey
                    print(f"\033[37mResponse from {
                          llm_model}:\n{result[:2000]}\033[0m")
                    # Append the result to the report file
                    # stromanbieter is the second part of the filename
                    Stromanbietername = f.split('_')[1]
                    report_file.write(
                        f"-- Stromanbieter: {Stromanbietername}\n{result}\n\n")
                    # Wait 2s
                    time.sleep(2)
                else:
                    print(f"Failed to get a response from {llm_model}.")
                    break
    return report_file_path


def solidify_report(report_file_path='Default', query_to_use='Standard', llm_model='arli_nemo', ending='solid.txt'):
    """
    Reads the content of a report file, sends it to the LLM for solidification
    using the specified query, and saves the solidified report to a new file.

    Args:
        report_file_path (str): The path to the report file.
        query_to_use (str): The name of the query to use for solidification.
        llm_model (str, optional): The name of the LLM model to use. Defaults to 'arli_nemo'.
    """
    try:
        with open(report_file_path, 'r', encoding='utf-8') as report_file:
            report_content = report_file.read()

        print(f"Analyzing report with {llm_model} and query: {query_to_use}")
        solidified_result = llm_analyze(
            llm_model, query_to_use, context=report_content)

        if solidified_result:
            # Create solidified report file
            solid_report_file_path = f'{os.path.splitext(report_file_path)[
                0]}_{ending}'
            with open(solid_report_file_path, 'w', encoding='utf-8') as solid_report_file:
                solid_report_file.write(solidified_result)
            print(f"Solidified report saved to: {solid_report_file_path}")
            return solid_report_file_path
        else:
            print(f"Failed to get a solidified response from {llm_model}.")
            return None
    except FileNotFoundError:
        print(f"Error: Report file not found at {report_file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def del_files(contains='report_', doesnotcontain=''):
    for f in os.listdir('data/crawls'):
        should_delete = True

        # Only check 'contains' if it's not empty
        if contains:
            should_delete = contains in f

        # Only check 'doesnotcontain' if it's not empty
        if should_delete and doesnotcontain:
            should_delete = doesnotcontain not in f

        if should_delete:
            try:
                full_path = os.path.join('data/crawls', f)
                os.remove(full_path)
            except OSError as e:
                print(f"Error deleting {f}: {e}")


if __name__ == '__main__':
    # Example usage:
    #    llm_model = 'openrouter_llama'
    #    llm_model = 'groq_r1'
    #    llm_model = 'amp1_gemma'
    # llm_model = 'arli_nemo'
    #    query_to_use = 'TARIFLISTE_ABFRAGE'
    # delete files starting with report_ and not containing solid

    if True:
        del_files(contains='report_', doesnotcontain='solid')
        report_file_path = llmanalyze_files(
            llm_model='mistral_large',
            files='crawl_',
            query_to_use='TARIFLISTE_ABFRAGE')

    if True:
        try:
            report_file_path
        except NameError:
            report_file_path = 'data/crawls/report_20250131.txt'
        del_files(contains='solid')
        solidify_report(
            report_file_path=report_file_path,
            query_to_use='TARIF_TABELLE',
            llm_model='groq_r1',
            ending='tab.md')
