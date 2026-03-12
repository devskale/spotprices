#!/usr/bin/env python3
"""
Test script to debug the specific file processing issue in llm_analyze.py
"""
import os
import sys
from pathlib import Path

# Add current directory to path so we can import our modules
sys.path.insert(0, '/Users/johannwaldherr/code/gwen.at/spotprices')

from llm_analyze import llm_analyze

def test_with_real_file():
    """Test LLM call with actual crawl file content"""
    
    print("=== TESTING WITH REAL CRAWL FILE ===")
    
    # Get the first crawl file
    crawl_dir = Path("data/crawls")
    if not crawl_dir.exists():
        print("❌ Crawl directory doesn't exist")
        return False
        
    crawl_files = list(crawl_dir.glob("crawl_*.txt"))
    if not crawl_files:
        print("❌ No crawl files found")
        return False
        
    print(f"Found {len(crawl_files)} crawl files")
    
    # Test with the first file
    test_file = crawl_files[0]
    print(f"Testing with: {test_file}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"File content length: {len(content)} characters")
        print(f"First 200 chars: {content[:200]}...")
        
        # Test LLM call with this content
        result = llm_analyze("big@glm", "TARIFLISTE_ABFRAGE", content)
        
        if result:
            print(f"✅ SUCCESS: Got response: {result[:300]}...")
            return True
        else:
            print(f"❌ FAILURE: No response from LLM")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_llm_call():
    """Test simple LLM call without file content"""
    print("=== TESTING SIMPLE LLM CALL ===")
    
    simple_context = """SmartEnergy tariff information:
    SmartEnergy Basic: 25.5 ct/kWh, Bezug, fixed price
    SmartEnergy Dynamic: EPEXAT + 2.5 ct/kWh, Bezug, variable price"""
    
    result = llm_analyze("big@glm", "TARIFLISTE_ABFRAGE", simple_context)
    
    if result:
        print(f"✅ SUCCESS: Simple call worked: {result[:300]}...")
        return True
    else:
        print(f"❌ FAILURE: Simple LLM call failed")
        return False

def test_minimal_query():
    """Test with the simplest possible query"""
    print("=== TESTING MINIMAL QUERY ===")
    
    result = llm_analyze("big@glm", "WIEN_ABFRAGE", None)
    
    if result:
        print(f"✅ SUCCESS: Minimal query worked: {result}")
        return True
    else:
        print(f"❌ FAILURE: Minimal query failed")
        return False

def check_file_permissions():
    """Check if we can read the crawl files"""
    print("=== CHECKING FILE PERMISSIONS ===")
    
    crawl_dir = Path("data/crawls")
    if not crawl_dir.exists():
        print("❌ Crawl directory doesn't exist")
        return False
        
    try:
        files = list(crawl_dir.glob("crawl_*.txt"))
        print(f"✅ Found {len(files)} files")
        
        for file_path in files[:3]:  # Check first 3 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)  # Just read first 100 chars
                print(f"✅ Can read {file_path.name}: {content[:50]}...")
            except Exception as e:
                print(f"❌ Cannot read {file_path.name}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error accessing crawl directory: {e}")
        return False

if __name__ == "__main__":
    print("File Processing Debug Script")
    print("============================")
    
    # Check file access first
    if not check_file_permissions():
        print("❌ Cannot access files, exiting")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Test minimal query first
    if test_minimal_query():
        print("\n" + "="*50)
        
        # Test simple call
        if test_simple_llm_call():
            print("\n" + "="*50)
            
            # Test with real file
            if test_with_real_file():
                print("\n🎉 ALL TESTS PASSED")
                sys.exit(0)
            else:
                print("\n❌ File processing test failed")
                sys.exit(1)
        else:
            print("\n❌ Simple LLM call test failed")
            sys.exit(1)
    else:
        print("\n❌ Minimal query test failed")
        sys.exit(1)