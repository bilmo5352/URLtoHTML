#!/usr/bin/env python3
"""
Example script to demonstrate URL to HTML conversion.

Edit the URL variable below to test different URLs.
"""

import logging
from url_to_html import fetch_html, FetcherConfig

# URL to fetch - change this to test different URLs
URL = "https://www.nykaa.com/brands/nykaa-cosmetics/c/1937?search_redirection=True"

# Setup logging to see the process
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def main():
    print(f"\nFetching HTML for: {URL}")
    print("=" * 60)
    
    try:
        # Create config with Decodo credentials for JS rendering
        # Replace with your actual Decodo credentials
        config = FetcherConfig(
            enable_logging=True,
            log_level=logging.INFO,
            # Decodo JS rendering credentials (uncomment and fill in)
            # js_username="U0000325820",
            # js_password="PW_19849a2d58cbbf2af5e39e3a38693d1ba",
            # js_timeout=180,
            # js_location="us",  # Optional
            # js_language="en-US",  # Optional
        )
        
        # Fetch HTML
        html = fetch_html(URL, config=config)
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print(f"Retrieved {len(html)} bytes of HTML")
        print("=" * 60)
        print("\nFirst 500 characters of HTML:")
        print("-" * 60)
        print(html[:500])
        if len(html) > 500:
            print("...")
        print("-" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)

if __name__ == "__main__":
    main()

