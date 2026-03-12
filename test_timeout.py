#!/usr/bin/env python3
"""
Test to confirm timeout issue and test with longer timeouts
"""
import os
import sys
import time
import pytest

if os.getenv("RUN_LLM_TESTS") != "1":
    pytest.skip("Set RUN_LLM_TESTS=1 to run live LLM tests.", allow_module_level=True)

sys.path.insert(0, '/Users/johannwaldherr/code/gwen.at/spotprices')

from config import LLM_CONFIG, QUERY_CONFIG, PASSWORDS
import requests

def test_timeout_issue():
    """Test LLM call with and without explicit timeout"""
    
    print("=== TESTING TIMEOUT ISSUE ===")
    
    # Load a sample of the large content
    from pathlib import Path
    crawl_files = sorted(Path("data/crawls").glob("crawl_*.txt"))
    if not crawl_files:
        pytest.skip("No crawl files available in data/crawls.", allow_module_level=False)
    with open(crawl_files[0], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use a smaller sample for testing
    test_content = content[:5000]  # 5000 chars
    print(f"Testing with {len(test_content)} characters")
    
    # Get configuration
    llm_model_name = "big@glm"
    query_name = "TARIFLISTE_ABFRAGE"
    
    llm_config = LLM_CONFIG.get(llm_model_name)
    query_config = QUERY_CONFIG.get(query_name)
    
    query = query_config[0].get("QUERY")
    query = f"{query}\n\n{test_content}"
    
    base_url = llm_config[0].get("BASEURL")
    api_key = PASSWORDS.get(llm_config[0].get("APIKEY"))
    model = llm_config[0].get("MODEL")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = {"model": model, "messages": [{"role": "user", "content": query}]}
    endpoint = f"{base_url}/chat/completions"
    
    print(f"Testing endpoint: {endpoint}")
    
    # Test 1: No timeout (default)
    print("\n--- Test 1: No timeout (default) ---")
    start_time = time.time()
    try:
        response = requests.post(endpoint, headers=headers, json=data)
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: {response.status_code} in {elapsed:.2f}s")
        if response.status_code == 200:
            result = response.json()
            print(f"Response keys: {list(result.keys())}")
        return True
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f}s: {e}")
        return False
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        print(f"❌ REQUEST ERROR after {elapsed:.2f}s: {e}")
        return False
    
    # Test 2: Short timeout (10s)
    print("\n--- Test 2: Short timeout (10s) ---")
    start_time = time.time()
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=10)
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: {response.status_code} in {elapsed:.2f}s")
        return True
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f}s: {e}")
        return False
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        print(f"❌ REQUEST ERROR after {elapsed:.2f}s: {e}")
        return False
    
    # Test 3: Long timeout (60s)
    print("\n--- Test 3: Long timeout (60s) ---")
    start_time = time.time()
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=60)
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: {response.status_code} in {elapsed:.2f}s")
        return True
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f}s: {e}")
        return False
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        print(f"❌ REQUEST ERROR after {elapsed:.2f}s: {e}")
        return False

def test_simple_quick_call():
    """Test a quick simple call to verify API is working"""
    
    print("\n=== TESTING QUICK SIMPLE CALL ===")
    
    llm_model_name = "big@glm"
    query_name = "WIEN_ABFRAGE"
    
    llm_config = LLM_CONFIG.get(llm_model_name)
    query_config = QUERY_CONFIG.get(query_name)
    
    query = query_config[0].get("QUERY")
    
    base_url = llm_config[0].get("BASEURL")
    api_key = PASSWORDS.get(llm_config[0].get("APIKEY"))
    model = llm_config[0].get("MODEL")
    
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = {"model": model, "messages": [{"role": "user", "content": query}]}
    endpoint = f"{base_url}/chat/completions"
    
    print(f"Testing simple query: {query[:50]}...")
    
    start_time = time.time()
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: {response.status_code} in {elapsed:.2f}s")
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"Response: {content[:100]}...")
        return True
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f}s: {e}")
        return False
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        print(f"❌ REQUEST ERROR after {elapsed:.2f}s: {e}")
        return False

if __name__ == "__main__":
    print("Timeout Issue Diagnosis")
    print("=======================")
    
    # Test quick call first
    simple_success = test_simple_quick_call()
    
    if simple_success:
        print("\n" + "="*50)
        # Test with larger content
        test_timeout_issue()
    else:
        print("❌ Simple call failed - API might be down")
    
    print("\n💡 CONCLUSION:")
    print("   - If simple call works but large content fails: TIMEOUT ISSUE")
    print("   - If both fail: API or network issue") 
    print("   - SOLUTION: Add timeout parameter to requests.post() calls")
