#!/usr/bin/env python3
"""
Test script to process 10 URLs in parallel using JSrend.

This demonstrates parallel processing with the current synchronous code
using ThreadPoolExecutor. Includes rate limiting to avoid 429 errors.
"""

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from url_to_html.js_renderer import JSrend

# Test URLs - replace with your actual URLs
TEST_URLS = [
    "https://www.walmart.com/search?query=turkey%20fryer",
    "https://www.meesho.com/search?q=kurthi",
    "https://www.flipkart.com/",
    "https://www.amazon.in/s?k=airpods+pro2",
    "https://www.nykaa.com/",
    "https://www.myntra.com/",
    "https://www.snapdeal.com/",
    "https://www.shopclues.com/",
    "https://www.paytm.com/",
    "https://www.bigbasket.com/",
]

# Semaphore to limit concurrent requests (rate limiting)
# IMPORTANT: Decodo can only process 3 URLs concurrently at a time
MAX_CONCURRENT = 3  # Decodo's limit - do not exceed
request_semaphore = Semaphore(MAX_CONCURRENT)

def process_url(url: str, delay: float = 0) -> dict:
    """
    Process a single URL and return result.
    
    Args:
        url: URL to process
        delay: Delay before starting (to stagger requests)
    """
    # Stagger requests to avoid hitting rate limits
    if delay > 0:
        time.sleep(delay)
    
    # Acquire semaphore to limit concurrent requests
    request_semaphore.acquire()
    start_time = time.time()
    
    try:
        html = JSrend(url)
        elapsed = time.time() - start_time
        result = {
            "url": url,
            "status": "success",
            "html_length": len(html),
            "elapsed_time": elapsed,
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "url": url,
            "status": "failed",
            "html_length": 0,
            "elapsed_time": elapsed,
            "error": str(e)
        }
    finally:
        # Release semaphore
        request_semaphore.release()
    
    return result

def main():
    print(f"Processing {len(TEST_URLS)} URLs in parallel...")
    print(f"Max concurrent requests: {MAX_CONCURRENT}")
    print("=" * 80)
    
    start_time = time.time()
    results = []
    
    # Stagger requests with small random delays to avoid rate limits
    delays = [random.uniform(0, 0.5) * i for i in range(len(TEST_URLS))]
    
    # Process URLs in parallel using ThreadPoolExecutor
    # Limit workers to MAX_CONCURRENT to respect rate limits
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        # Submit all tasks with staggered delays
        future_to_url = {
            executor.submit(process_url, url, delay): url 
            for url, delay in zip(TEST_URLS, delays)
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            
            status_icon = "✓" if result["status"] == "success" else "✗"
            print(f"{status_icon} {result['url'][:50]:<50} | "
                  f"Status: {result['status']:<8} | "
                  f"Size: {result['html_length']:>8} bytes | "
                  f"Time: {result['elapsed_time']:.2f}s")
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    avg_time = sum(r["elapsed_time"] for r in results) / len(results)
    
    print(f"Total URLs: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per URL: {avg_time:.2f}s")
    print(f"Throughput: {len(results)/total_time:.2f} URLs/second")
    print("=" * 80)
    
    # Show errors if any
    errors = [r for r in results if r["error"]]
    if errors:
        print("\nERRORS:")
        for r in errors:
            print(f"  - {r['url']}: {r['error']}")

if __name__ == "__main__":
    main()

