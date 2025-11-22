"""
Example demonstrating massive scaling with the URL to HTML Converter API.

This example shows how to:
- Process thousands of URLs
- Configure for maximum parallelism
- Use multiple custom JS rendering services
- Monitor progress and performance
"""

from client import URLToHTMLClient
import time

def main():
    # Initialize client with longer timeout for large batches
    client = URLToHTMLClient(
        base_url="http://localhost:8000",
        timeout=7200  # 2 hours for very large batches
    )
    
    # Generate a large list of URLs (example)
    # In production, you would load these from a file or database
    urls = [
        f"https://example.com/page{i}" 
        for i in range(1000)  # 1000 URLs
    ]
    
    # Configure for massive scaling
    # Add as many custom JS services as you have available
    custom_js_services = [
        "easygoing-strength-copy-2-copy-2-production.up.railway.app",
        "easygoing-strength-copy-2-copy-1-production.up.railway.app",
        "easygoing-strength-copy-copy-1-production.up.railway.app",
        "easygoing-strength-copy-2-copy-production.up.railway.app",
        "easygoing-strength-copy-2-production.up.railway.app",
        "easygoing-strength-copy-production.up.railway.app",
        "easygoing-strength-copy-1-production.up.railway.app",
        "easygoing-strength-copy-copy-production.up.railway.app",
        "easygoing-strength-production-d985.up.railway.app",
        "easygoing-strength-copy-3-production.up.railway.app",
        "easygoing-strength-copy-copy-copy-2-production.up.railway.app",
        "easygoing-strength-copy-copy-copy-production.up.railway.app",
        "easygoing-strength-copy-copy-copy-1-production.up.railway.app",
        # Add more services here as you deploy them
        # "service14.com",
        # "service15.com",
        # ... up to 100+ services for massive scaling
    ]
    
    print(f"Processing {len(urls)} URLs with {len(custom_js_services)} custom JS services")
    print(f"Expected parallel capacity: {len(custom_js_services) * 20} URLs simultaneously")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Check API health first
        health = client.health_check()
        print(f"API Status: {health['status']}")
        print(f"API Version: {health['version']}")
        print()
        
        # Fetch batch with massive scaling configuration
        print("Starting batch processing...")
        response = client.fetch_batch(
            urls,
            static_xhr_concurrency=200,  # Process 200 URLs in parallel for static/XHR
            custom_js_service_endpoints=custom_js_services,
            custom_js_batch_size=20,  # 20 URLs per service batch
            custom_js_cooldown_seconds=120,  # 2 minute cooldown
            decodo_enabled=True  # Enable Decodo fallback
        )
        
        elapsed_time = time.time() - start_time
        
        # Print detailed summary
        print("\n" + "=" * 60)
        print("BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total URLs: {response.summary.total}")
        print(f"Successful: {response.summary.success}")
        print(f"Failed: {response.summary.failed}")
        print(f"Success Rate: {response.summary.success_rate:.2f}%")
        print(f"Processing Time: {response.summary.total_time:.2f}s")
        print(f"Total Elapsed Time: {elapsed_time:.2f}s")
        print(f"\nResults by Method:")
        for method, count in sorted(response.summary.by_method.items()):
            percentage = (count / response.summary.total) * 100
            print(f"  {method:15s}: {count:5d} ({percentage:5.2f}%)")
        
        # Performance metrics
        if response.summary.total > 0:
            urls_per_second = response.summary.total / response.summary.total_time
            print(f"\nPerformance:")
            print(f"  URLs per second: {urls_per_second:.2f}")
            print(f"  Average time per URL: {response.summary.total_time / response.summary.total:.2f}s")
        
        # Show some successful results
        successful = response.get_successful()
        if successful:
            print(f"\nSample Successful Results (first 5):")
            for result in successful[:5]:
                print(f"  ✓ {result.url}")
                print(f"    Method: {result.method}, Size: {len(result.html)} bytes")
        
        # Show failed results
        failed = response.get_failed()
        if failed:
            print(f"\nFailed Results ({len(failed)}):")
            for result in failed[:10]:  # Show first 10 failures
                print(f"  ✗ {result.url}")
                print(f"    Error: {result.error}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more failures")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    main()

