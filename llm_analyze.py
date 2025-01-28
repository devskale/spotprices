import requests
import json
from config import LLM_CONFIG, QUERY_CONFIG

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
    api_key = llm_config[0].get("APIKEY")
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
    else :  # openai fallback
         headers['Authorization'] = f'Bearer {api_key}'
         data = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }


    try:
        if 'openrouter' in llm_model_name:
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data)
        elif 'amp1' in llm_model_name:
            response = requests.post(f"{base_url}/v1/completions", headers=headers, json=data)
        else:
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data)
            
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


if __name__ == '__main__':
    # Example usage:
#    llm_model = 'openrouter_llama'
    llm_model = 'groq_r1'
#    llm_model = 'amp1_gemma'
#    llm_model = 'arli_nemo'
    query_to_use = 'TARIFLISTE_ABFRAGE'
    
    # Example context
    with open('data/crawls/test3.txt', 'r') as file:
        example_context = file.read()

    maxtokens = 12000
    tokens = round(len(example_context) / 4)
    if tokens > maxtokens:
        print(f"Context is too long ({tokens} tokens). Truncated at {maxtokens} tokens.")
        example_context = example_context[:maxtokens * 4]
    else:
        print(f"Context: {tokens} tokens.")

    #exit()

    result = llm_analyze(llm_model, query_to_use, context=example_context)

    if result:
        print(f"Response from {llm_model}:\n{result}")
    else:
        print(f"Failed to get a response from {llm_model}.")
