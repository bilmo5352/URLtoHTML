"""
Basic example using the URL to HTML Converter API client.

This example demonstrates:
- Initializing the client
- Fetching a batch of URLs
- Processing results
- Error handling
"""

from client import URLToHTMLClient

def main():
    # Initialize client
    client = URLToHTMLClient(base_url="http://localhost:8000")
    
    # List of URLs to fetch
    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://github.com"
    ]
    
    print(f"Fetching HTML for {len(urls)} URLs...")
    print("-" * 60)
    
    try:
        # Fetch batch
        response = client.fetch_batch(urls)
        
        # Print summary
        print(f"\nSummary:")
        print(f"  Total: {response.summary.total}")
        print(f"  Success: {response.summary.success}")
        print(f"  Failed: {response.summary.failed}")
        print(f"  Success Rate: {response.summary.success_rate:.2f}%")
        print(f"  Processing Time: {response.summary.total_time:.2f}s")
        print(f"\nResults by Method:")
        for method, count in response.summary.by_method.items():
            print(f"  {method}: {count}")
        
        # Print individual results
        print(f"\nIndividual Results:")
        for result in response.results:
            if result.is_success:
                print(f"  ✓ {result.url}")
                print(f"    Method: {result.method}")
                print(f"    Size: {len(result.html)} bytes")
            else:
                print(f"  ✗ {result.url}")
                print(f"    Error: {result.error}")
        
        # Get successful results
        successful = response.get_successful()
        print(f"\n{len(successful)} URLs fetched successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Cleanup
        client.close()

if __name__ == "__main__":
    main()

