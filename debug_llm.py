#!/usr/bin/env python3
"""
Debug script to test LLM API calls and identify the failure point
"""
import json
import requests
import sys
from config import LLM_CONFIG, QUERY_CONFIG, PASSWORDS

def debug_llm_call(llm_model_name, query_name, context=None):
    """Debug version of llm_analyze with detailed logging"""
    
    print(f"\n=== DEBUGGING LLM CALL ===")
    print(f"Model: {llm_model_name}")
    print(f"Query: {query_name}")
    print(f"Has context: {context is not None}")
    if context:
        print(f"Context length: {len(context)} chars")
    
    # Get LLM configuration
    llm_config = LLM_CONFIG.get(llm_model_name)
    if not llm_config:
        print(f"❌ ERROR: No configuration found for LLM model: {llm_model_name}")
        return None
        
    print(f"✅ LLM config found: {llm_config}")
    
    # Get query configuration
    query_config = QUERY_CONFIG.get(query_name)
    if not query_config:
        print(f"❌ ERROR: No query found for query name: {query_name}")
        return None
        
    print(f"✅ Query config found")
    
    query = query_config[0].get("QUERY")
    print(f"✅ Query template retrieved (length: {len(query)})")
    
    # Add context to the query if provided
    if context:
        query = f"{query}\n\n{context}"
        print(f"✅ Context added to query (total length: {len(query)})")
    
    # Get API configuration
    base_url = llm_config[0].get("BASEURL")
    api_key_handle = llm_config[0].get("APIKEY")
    model = llm_config[0].get("MODEL")
    
    print(f"Base URL: {base_url}")
    print(f"API Key Handle: {api_key_handle}")
    print(f"Model: {model}")
    
    api_key = PASSWORDS.get(api_key_handle)
    if not api_key:
        print(f"❌ ERROR: No API key found for {api_key_handle}")
        return None
        
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Test connectivity
    print(f"\n=== TESTING CONNECTIVITY ===")
    try:
        test_response = requests.get(base_url, timeout=5)
        print(f"✅ API endpoint reachable: {test_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Cannot reach API endpoint: {e}")
        print(f"   URL: {base_url}")
        return None
    
    # Prepare request
    headers = {"Content-Type": "application/json"}
    
    # Determine provider type from model name
    if 'openrouter' in llm_model_name:
        headers['Authorization'] = f'Bearer {api_key}'
        data = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }
        endpoint = f"{base_url}/chat/completions"
        print(f"Using OpenRouter format")
        
    elif 'amp1' in llm_model_name:
        data = {
            "prompt": query,
            "model": model
        }
        endpoint = f"{base_url}/v1/completions"
        print(f"Using Amp1 format")
        
    else:  # Default/other format
        headers['Authorization'] = f'Bearer {api_key}'
        data = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }
        endpoint = f"{base_url}/chat/completions"
        print(f"Using default/other format")
    
    print(f"Endpoint: {endpoint}")
    print(f"Request data keys: {list(data.keys())}")
    
    # Make the request
    print(f"\n=== MAKING REQUEST ===")
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: API returned error status {response.status_code}")
            print(f"Response text: {response.text}")
            return None
            
        response_json = response.json()
        print(f"✅ Response JSON keys: {list(response_json.keys())}")
        
        # Parse response based on provider
        if 'openrouter' in llm_model_name:
            if 'choices' in response_json and len(response_json['choices']) > 0:
                result = response_json['choices'][0]['message']['content']
                print(f"✅ OpenRouter response parsed successfully")
                return result
            else:
                print(f"❌ ERROR: Invalid OpenRouter response structure")
                print(f"Response: {response_json}")
                return None
                
        elif 'amp1' in llm_model_name:
            if 'choices' in response_json and len(response_json['choices']) > 0:
                result = response_json['choices'][0]['text']
                print(f"✅ Amp1 response parsed successfully")
                return result
            else:
                print(f"❌ ERROR: Invalid Amp1 response structure")
                print(f"Response: {response_json}")
                return None
        else:
            # Default format
            if 'choices' in response_json and len(response_json['choices']) > 0:
                result = response_json['choices'][0]['message']['content']
                print(f"✅ Default response parsed successfully")
                return result
            else:
                print(f"❌ ERROR: Invalid default response structure")
                print(f"Response: {response_json}")
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed: {e}")
        return None
    except KeyError as e:
        print(f"❌ ERROR: KeyError parsing response: {e}")
        try:
            print(f"Raw response: {response.text}")
        except:
            pass
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON response: {e}")
        print(f"Response text: {response.text}")
        return None

def test_simple_query():
    """Test with a simple query"""
    print("=== TESTING SIMPLE QUERY ===")
    
    # Test with minimal context
    simple_context = "This is a test context with some sample data."
    
    result = debug_llm_call("big@glm", "WIEN_ABFRAGE", simple_context)
    
    if result:
        print(f"\n✅ SUCCESS: Got response: {result[:200]}...")
        return True
    else:
        print(f"\n❌ FAILURE: No response received")
        return False

if __name__ == "__main__":
    print("LLM Debug Script")
    print("================")
    
    # Test simple query
    success = test_simple_query()
    
    if not success:
        print(f"\n🔍 ADDITIONAL DIAGNOSTICS:")
        print(f"Available LLM models: {list(LLM_CONFIG.keys())}")
        print(f"Available queries: {list(QUERY_CONFIG.keys())}")
        print(f"Available API keys: {list(PASSWORDS.keys())}")
    
    sys.exit(0 if success else 1)