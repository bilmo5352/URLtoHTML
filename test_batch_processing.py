#!/usr/bin/env python3
"""
Test script for batch processing 100+ URLs with all fallbacks.
"""

import asyncio
import logging
from url_to_html.async_batch_fetcher import async_fetch_batch
from url_to_html.batch_config import BatchFetcherConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# Test URLs - mix of different domains
TEST_URLS = [
    # Flipkart URLs (20)
    "https://www.flipkart.com/search?q=tablets",
    "https://www.flipkart.com/search?q=speakers",
    "https://www.flipkart.com/search?q=keyboards",
    "https://www.flipkart.com/search?q=mice",
    "https://www.flipkart.com/search?q=monitors",
    "https://www.flipkart.com/search?q=printers",
    "https://www.flipkart.com/search?q=hard+drives",
    "https://www.flipkart.com/search?q=pendrives",
    "https://www.flipkart.com/search?q=chargers",
    "https://www.flipkart.com/search?q=cables",
    "https://www.flipkart.com/search?q=webcams",
    "https://www.flipkart.com/search?q=usb+hubs",
    "https://www.flipkart.com/search?q=power+banks",
    "https://www.flipkart.com/search?q=wireless+chargers",
    "https://www.flipkart.com/search?q=headphones",
    "https://www.flipkart.com/search?q=earphones",
    "https://www.flipkart.com/search?q=bluetooth+speakers",
    "https://www.flipkart.com/search?q=smart+watches",
    "https://www.flipkart.com/search?q=fitness+bands",
    "https://www.flipkart.com/search?q=smartphones",
    
    # Amazon URLs (20)
    "https://www.amazon.in/s?k=webcams",
    "https://www.amazon.in/s?k=usb+hubs",
    "https://www.amazon.in/s?k=power+banks",
    "https://www.amazon.in/s?k=wireless+chargers",
    "https://www.amazon.in/s?k=laptops",
    "https://www.amazon.in/s?k=tablets",
    "https://www.amazon.in/s?k=smartphones",
    "https://www.amazon.in/s?k=headphones",
    "https://www.amazon.in/s?k=speakers",
    "https://www.amazon.in/s?k=keyboards",
    "https://www.amazon.in/s?k=mice",
    "https://www.amazon.in/s?k=monitors",
    "https://www.amazon.in/s?k=printers",
    "https://www.amazon.in/s?k=hard+drives",
    "https://www.amazon.in/s?k=pendrives",
    "https://www.amazon.in/s?k=chargers",
    "https://www.amazon.in/s?k=cables",
    "https://www.amazon.in/s?k=smart+watches",
    "https://www.amazon.in/s?k=fitness+bands",
    "https://www.amazon.in/s?k=bluetooth+speakers",
    
    # Nykaa URLs (15)
    "https://www.nykaa.com/skin/sunscreens/c/8394",
    "https://www.nykaa.com/hair/hair-care/conditioner/c/1222",
    "https://www.nykaa.com/makeup/cheeks/blush/c/747",
    "https://www.nykaa.com/skin/moisturizers/c/8386",
    "https://www.nykaa.com/makeup/lips/lipstick/c/744",
    "https://www.nykaa.com/hair/hair-care/shampoo/c/1221",
    "https://www.nykaa.com/skin/cleansers/c/8381",
    "https://www.nykaa.com/makeup/eyes/eyeliner/c/751",
    "https://www.nykaa.com/makeup/face/foundation/c/748",
    "https://www.nykaa.com/skin/toners/c/8382",
    "https://www.nykaa.com/hair/hair-care/hair+masks/c/1223",
    "https://www.nykaa.com/makeup/cheeks/highlighter/c/749",
    "https://www.nykaa.com/skin/serums/c/8383",
    "https://www.nykaa.com/makeup/eyes/mascara/c/752",
    "https://www.nykaa.com/skin/face-wash/c/8380",
    
    # Myntra URLs (10)
    "https://www.myntra.com/women-jeans",
    "https://www.myntra.com/men-shoes",
    "https://www.myntra.com/women-shoes",
    "https://www.myntra.com/men-tshirts",
    "https://www.myntra.com/women-dresses",
    "https://www.myntra.com/men-shirts",
    "https://www.myntra.com/women-handbags",
    "https://www.myntra.com/men-watches",
    "https://www.myntra.com/women-watches",
    "https://www.myntra.com/men-jeans",
    
    # Meesho URLs (10)
    "https://www.meesho.com/search?q=kurthi",
    "https://www.meesho.com/search?q=saree",
    "https://www.meesho.com/search?q=dress",
    "https://www.meesho.com/search?q=shirt",
    "https://www.meesho.com/search?q=jeans",
    "https://www.meesho.com/search?q=shoes",
    "https://www.meesho.com/search?q=bag",
    "https://www.meesho.com/search?q=watch",
    "https://www.meesho.com/search?q=jewellery",
    "https://www.meesho.com/search?q=makeup",
    
    # Other URLs (25)
    "https://www.snapdeal.com/",
    "https://www.shopclues.com/",
    "https://www.paytm.com/",
    "https://www.bigbasket.com/",
    "https://www.zomato.com/",
    "https://www.swiggy.com/",
    "https://www.uber.com/",
    "https://www.olacabs.com/",
    "https://www.bookmyshow.com/",
    "https://www.makemytrip.com/",
    "https://www.goibibo.com/",
    "https://www.cleartrip.com/",
    "https://www.redbus.in/",
    "https://www.irctc.co.in/",
    "https://www.phonepe.com/",
    "https://www.gpay.com/",
    "https://www.razorpay.com/",
    "https://www.cred.com/",
    "https://www.groww.in/",
    "https://www.zerodha.com/",
    "https://www.upstox.com/",
    "https://www.byjus.com/",
    "https://www.vedantu.com/",
    "https://www.unacademy.com/",
    "https://www.coursera.org/",
]


async def main():
    print(f"\n{'='*80}")
    print(f"BATCH PROCESSING TEST - {len(TEST_URLS)} URLs")
    print(f"{'='*80}\n")
    
    # Create configuration
    config = BatchFetcherConfig(
        static_xhr_concurrency=50,
        custom_js_api_url="https://easygoing-strength-production-d985.up.railway.app/render",
        custom_js_batch_size=20,
        custom_js_cooldown_seconds=120,
        decodo_enabled=True,
        save_outputs=True,
        enable_logging=True
    )
    
    try:
        # Process batch
        result = await async_fetch_batch(TEST_URLS, config)
        
        # Display results
        print(f"\n{'='*80}")
        print("FINAL RESULTS")
        print(f"{'='*80}\n")
        
        summary = result["summary"]
        print(f"Total URLs: {summary['total']}")
        print(f"✅ Successful: {summary['success']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"\nBy Method:")
        for method, count in summary['by_method'].items():
            print(f"  - {method}: {count}")
        print(f"\nJS Batches Processed: {summary['js_batches_processed']}")
        print(f"Decodo Fallback Count: {summary['decodo_fallback_count']}")
        print(f"Total Time: {summary['total_time']:.2f} seconds")
        print(f"Average Time per URL: {summary['total_time']/summary['total']:.2f} seconds")
        
        # Show failed URLs
        failed = [r for r in result["results"] if r["status"] == "failed"]
        if failed:
            print(f"\n{'='*80}")
            print(f"FAILED URLs ({len(failed)}):")
            print(f"{'='*80}")
            for r in failed:
                print(f"  - {r['url']}")
                print(f"    Method: {r['method'] or 'N/A'}")
                print(f"    Error: {r['error']}")
        
        print(f"\n{'='*80}")
        print("TEST COMPLETED")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

