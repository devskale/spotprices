#!/usr/bin/env python3
"""
Test to find the exact content size threshold where LLM calls fail
"""
import os
import sys
import pytest
from pathlib import Path

if os.getenv("RUN_LLM_TESTS") != "1":
    pytest.skip("Set RUN_LLM_TESTS=1 to run live LLM tests.", allow_module_level=True)

sys.path.insert(0, '/Users/johannwaldherr/code/gwen.at/spotprices')

from llm_analyze import llm_analyze

def test_content_size_threshold():
    """Test with progressively larger content to find failure threshold"""
    
    print("=== TESTING CONTENT SIZE THRESHOLD ===")
    
    # Load the real crawl file content
    crawl_files = sorted(Path("data/crawls").glob("crawl_*.txt"))
    if not crawl_files:
        pytest.skip("No crawl files available in data/crawls.", allow_module_level=False)
    with open(crawl_files[0], 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    print(f"Total content length: {len(full_content)} characters")
    
    # Test with different content sizes
    test_sizes = [100, 500, 1000, 2000, 5000, 10000, 15000, len(full_content)]
    
    for size in test_sizes:
        if size > len(full_content):
            size = len(full_content)
            
        print(f"\n--- Testing with {size} characters ---")
        test_content = full_content[:size]
        
        print(f"Content preview: {test_content[:100]}...")
        
        result = llm_analyze("big@glm", "TARIFLISTE_ABFRAGE", test_content)
        
        if result:
            print(f"✅ SUCCESS: {len(result)} chars response")
            print(f"Response preview: {result[:100]}...")
        else:
            print(f"❌ FAILURE: No response at {size} characters")
            print(f"This suggests the limit is around {size} characters")
            return size
    
    return None

def test_with_truncated_content():
    """Test with the original 12000 token limit approach"""
    
    print("\n=== TESTING WITH ORIGINAL TOKEN LIMIT ===")
    
    # Load the real crawl file content
    crawl_files = sorted(Path("data/crawls").glob("crawl_*.txt"))
    if not crawl_files:
        pytest.skip("No crawl files available in data/crawls.", allow_module_level=False)
    with open(crawl_files[0], 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    # Apply the original token limit logic: 12000 tokens * 4 chars/token = 48000 chars
    # But since we know it fails around some point, let's try smaller limits
    maxtokens = 3000
    max_chars = maxtokens * 4  # 12000 chars
    
    print(f"Applying token limit: {maxtokens} tokens = {max_chars} chars")
    
    if len(full_content) > max_chars:
        test_content = full_content[:max_chars]
        print(f"Content truncated from {len(full_content)} to {len(test_content)} chars")
    else:
        test_content = full_content
        print(f"Content within limits: {len(test_content)} chars")
    
    result = llm_analyze("big@glm", "TARIFLISTE_ABFRAGE", test_content)
    
    if result:
        print("✅ SUCCESS with token-limited content")
        print(f"Response: {result[:200]}...")
        return True
    else:
        print("❌ FAILURE even with token-limited content")
        return False

def test_simplified_content():
    """Test with cleaned/simplified content"""
    
    print("\n=== TESTING WITH SIMPLIFIED CONTENT ===")
    
    # Load the real crawl file content
    crawl_files = sorted(Path("data/crawls").glob("crawl_*.txt"))
    if not crawl_files:
        pytest.skip("No crawl files available in data/crawls.", allow_module_level=False)
    with open(crawl_files[0], 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    # Try extracting just the meaningful parts
    # Look for tariff-related content
    lines = full_content.split('\n')
    tariff_lines = []
    
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['tarif', 'preis', 'strom', 'kwh', 'ct/kwh', 'smartcontrol']):
            if len(line) > 10:  # Filter out very short lines
                tariff_lines.append(line)
    
    simplified_content = '\n'.join(tariff_lines[:50])  # Take first 50 relevant lines
    print(f"Simplified content: {len(simplified_content)} chars")
    print(f"Simplified preview: {simplified_content[:200]}...")
    
    result = llm_analyze("big@glm", "TARIFLISTE_ABFRAGE", simplified_content)
    
    if result:
        print("✅ SUCCESS with simplified content")
        print(f"Response: {result[:200]}...")
        return True
    else:
        print("❌ FAILURE with simplified content")
        return False

if __name__ == "__main__":
    print("Content Size Threshold Test")
    print("===========================")
    
    # Test with progressively larger content
    limit = test_content_size_threshold()
    
    if limit:
        print(f"\n🔍 CONTENT SIZE LIMIT IDENTIFIED: ~{limit} characters")
        print("💡 SOLUTION: Implement proper content truncation")
    else:
        print("\n✅ No content size limit found - all tests passed")
    
    print("\n" + "="*50)
    
    # Test with original token limit
    test_with_truncated_content()
    
    print("\n" + "="*50)
    
    # Test with simplified content
    test_simplified_content()
