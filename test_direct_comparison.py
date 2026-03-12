#!/usr/bin/env python3
"""
Direct comparison test to identify the exact difference between working and failing calls
"""
import os
import sys
import json
import pytest

if os.getenv("RUN_LLM_TESTS") != "1":
    pytest.skip("Set RUN_LLM_TESTS=1 to run live LLM tests.", allow_module_level=True)

sys.path.insert(0, '/Users/johannwaldherr/code/gwen.at/spotprices')

from config import LLM_CONFIG, QUERY_CONFIG, PASSWORDS
import requests

def test_exact_same_call():
    """Test using exactly the same parameters as the debug script that worked"""
    
    print("=== EXACT SAME CALL AS DEBUG SCRIPT ===")
    
    llm_model_name = "big@glm"
    query_name = "WIEN_ABFRAGE"
    context = "This is a test context with some sample data."
    
    print(f"Model: {llm_model_name}")
    print(f"Query: {query_name}")
    print(f"Context: {context}")
    
    # Get LLM configuration
    llm_config = LLM_CONFIG.get(llm_model_name)
    print(f"LLM config: {llm_config}")
    
    # Get query configuration  
    query_config = QUERY_CONFIG.get(query_name)
    print(f"Query config found: {query_config is not None}")
    
    query = query_config[0].get("QUERY")
    print(f"Base query length: {len(query)}")
    
    # Add context to the query if provided
    if context:
        query = f"{query}\n\n{context}"
        print(f"Query with context length: {len(query)}")
    
    # Get API configuration
    base_url = llm_config[0].get("BASEURL")
    api_key_handle = llm_config[0].get("APIKEY")
    model = llm_config[0].get("MODEL")
    
    print(f"Base URL: {base_url}")
    print(f"API Key Handle: {api_key_handle}")
    print(f"Model: {model}")
    
    api_key = PASSWORDS.get(api_key_handle)
    print(f"API key: {api_key}")
    
    # Prepare request - EXACTLY like debug script
    headers = {"Content-Type": "application/json"}
    # Add authorization header (this was missing!)
    headers['Authorization'] = f'Bearer {api_key}'
    data = {
        "model": model,
        "messages": [{"role": "user", "content": query}]
    }
    
    endpoint = f"{base_url}/chat/completions"
    print(f"Endpoint: {endpoint}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    # Make the request
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_json = response.json()
            result = response_json['choices'][0]['message']['content']
            print(f"✅ SUCCESS: {result[:100]}...")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def test_without_context():
    """Test without context like in timeout test"""
    
    print("\n=== TEST WITHOUT CONTEXT (LIKE TIMEOUT TEST) ===")
    
    llm_model_name = "big@glm"
    query_name = "WIEN_ABFRAGE"
    
    # Get configuration
    llm_config = LLM_CONFIG.get(llm_model_name)
    query_config = QUERY_CONFIG.get(query_name)
    
    query = query_config[0].get("QUERY")
    # Don't add context
    
    base_url = llm_config[0].get("BASEURL")
    api_key = PASSWORDS.get(llm_config[0].get("APIKEY"))
    model = llm_config[0].get("MODEL")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = {
        "model": model,
        "messages": [{"role": "user", "content": query}]
    }
    
    endpoint = f"{base_url}/chat/completions"
    
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            result = response_json['choices'][0]['message']['content']
            print(f"✅ SUCCESS: {result[:100]}...")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    print("Direct Comparison Test")
    print("======================")
    
    # Test with context (should work)
    test_exact_same_call()
    
    print("\n" + "="*50)
    
    # Test without context (to see if that's the difference)
    test_without_context()
