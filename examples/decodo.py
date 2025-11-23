"""
Simple example client for URL to HTML Converter API.

This is a standalone example - just copy and use it!
Fetches HTML from URLs and saves them to files in the examples folder.
"""

import requests
import json
import os
from urllib.parse import urlparse
import re

# Configuration
API_URL = "https://urltohtml-production.up.railway.app/api/v1/fetch-batch"

# Your URLs to process
urls = [
        "https://www.meesho.com/search?q=saree"
]

# Function to save HTML to file
def save_html(url, html_content, method):
    """Save HTML content to a file in the examples folder."""
    # Create a safe filename from the URL
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = 'index'
    
    # Remove any special characters
    filename = re.sub(r'[^\w\-_]', '_', f"{method}_{domain}_{path}")
    filename = f"{filename}.html"
    
    # Save to examples folder (same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"    💾 Saved to: {filename}")
        return filepath
    except Exception as e:
        print(f"    ❌ Failed to save: {e}")
        return None

# Make the request
print(f"Sending {len(urls)} URLs to API...")
print(f"API: {API_URL}")
print()

response = requests.post(
    API_URL,
    json={"urls": urls},
    timeout=3600  # 1 hour timeout
)

# Check if request was successful
if response.status_code == 200:
    data = response.json()
    
    # Print summary
    summary = data["summary"]
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total URLs: {summary['total']}")
    print(f"Successful: {summary['success']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary.get('success_rate', 0):.2f}%")
    print(f"Total Time: {summary['total_time']:.2f} seconds")
    print()
    
    # Print results by method
    print("Results by Method:")
    for method, count in summary.get('by_method', {}).items():
        print(f"  {method}: {count}")
    print()
    
    # Show successful URLs and save HTML
    successful = [r for r in data["results"] if r["status"] == "success"]
    if successful:
        print(f"Successful URLs ({len(successful)}):")
        for result in successful:
            html_size = len(result.get("html", ""))
            print(f"  ✓ {result['url']}")
            print(f"    Method: {result['method']}, Size: {html_size:,} bytes")
            
            # Save HTML to file
            if result.get("html"):
                save_html(result['url'], result['html'], result['method'])
            
            print()
    
    # Show failed URLs
    failed = [r for r in data["results"] if r["status"] == "failed"]
    if failed:
        print(f"Failed URLs ({len(failed)}):")
        for result in failed:
            print(f"  ✗ {result['url']}")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            print()
    
    # Access HTML content
    print("=" * 60)
    print("HOW TO ACCESS HTML CONTENT")
    print("=" * 60)
    print()
    print("For each successful result:")
    print("  result['html']  # Contains the HTML content")
    print()
    print("Example:")
    if successful:
        first_result = successful[0]
        print(f"  URL: {first_result['url']}")
        print(f"  HTML length: {len(first_result.get('html', ''))} characters")
        print(f"  First 100 chars: {first_result.get('html', '')[:100]}...")
        print()
        print("✅ HTML files saved in the examples folder!")
    
else:
    print(f"Error: API returned status {response.status_code}")
    print(f"Response: {response.text}")

