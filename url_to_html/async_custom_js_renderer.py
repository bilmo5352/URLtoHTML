"""
Async batch processor for custom JS rendering service.
Processes URLs in batches of 20 with 2-minute cooldown between batches.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from .exceptions import JSRenderError

logger = logging.getLogger(__name__)


class AsyncCustomJSRenderer:
    """Batch processor for custom JS rendering service."""
    
    def __init__(
        self,
        api_url: str = "https://chromeworkers-copy-production.up.railway.app/render",
        batch_size: int = 20,
        cooldown_seconds: int = 120,  # 2 minutes
        timeout: int = 300  # 5 minutes for batch processing
    ):
        """
        Initialize the custom JS renderer.
        
        Args:
            api_url: Custom JS rendering API endpoint
            batch_size: Number of URLs to process per batch (default: 20)
            cooldown_seconds: Seconds to wait after each batch (default: 120 = 2 minutes)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.batch_size = batch_size
        self.cooldown_seconds = cooldown_seconds
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def _process_batch(
        self,
        session: aiohttp.ClientSession,
        urls: List[str],
        batch_num: int
    ) -> List[Dict[str, any]]:
        """
        Process a single batch of URLs.
        
        Args:
            session: aiohttp session
            urls: List of URLs to process (up to batch_size)
            batch_num: Batch number for logging
            
        Returns:
            List of result dictionaries
        """
        logger.info(f"Processing JS rendering batch {batch_num} with {len(urls)} URLs")
        
        try:
            payload = {"urls": urls}
            
            async with session.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"JS rendering API returned status {response.status}: {error_text}")
                    # Return failed results for all URLs in batch
                    return [
                        {
                            "url": url,
                            "html": None,
                            "status": "failed",
                            "error": f"API returned status {response.status}: {error_text[:200]}"
                        }
                        for url in urls
                    ]
                
                data = await response.json()
                
                # Process results
                results = []
                if "results" in data:
                    for result in data["results"]:
                        results.append({
                            "url": result.get("url", ""),
                            "html": result.get("html") if result.get("status") == "success" else None,
                            "status": result.get("status", "failed"),
                            "error": result.get("error") if result.get("status") != "success" else None
                        })
                else:
                    # Unexpected response format
                    logger.warning(f"Unexpected response format from JS rendering API")
                    return [
                        {
                            "url": url,
                            "html": None,
                            "status": "failed",
                            "error": "Unexpected response format from API"
                        }
                        for url in urls
                    ]
                
                successful = sum(1 for r in results if r["status"] == "success")
                failed = len(results) - successful
                logger.info(f"Batch {batch_num} completed: {successful} successful, {failed} failed")
                
                return results
                
        except asyncio.TimeoutError:
            logger.error(f"JS rendering batch {batch_num} timed out")
            return [
                {
                    "url": url,
                    "html": None,
                    "status": "failed",
                    "error": "Request timeout"
                }
                for url in urls
            ]
        except Exception as e:
            logger.error(f"JS rendering batch {batch_num} failed: {e}")
            return [
                {
                    "url": url,
                    "html": None,
                    "status": "failed",
                    "error": str(e)
                }
                for url in urls
            ]
    
    async def process_urls(
        self,
        urls: List[str]
    ) -> List[Dict[str, any]]:
        """
        Process URLs in batches with cooldown periods.
        
        Args:
            urls: List of URLs that need JS rendering
            
        Returns:
            List of result dictionaries with html, status, and error fields
        """
        if not urls:
            return []
        
        # Split URLs into batches
        batches = []
        for i in range(0, len(urls), self.batch_size):
            batch = urls[i:i + self.batch_size]
            batches.append(batch)
        
        logger.info(f"Processing {len(urls)} URLs in {len(batches)} batches of up to {self.batch_size} URLs")
        
        all_results = []
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for batch_num, batch_urls in enumerate(batches, 1):
                # Process batch
                batch_results = await self._process_batch(session, batch_urls, batch_num)
                all_results.extend(batch_results)
                
                # Cooldown after each batch (except the last one)
                if batch_num < len(batches):
                    logger.info(f"Waiting {self.cooldown_seconds} seconds before next batch (cooldown)...")
                    await asyncio.sleep(self.cooldown_seconds)
        
        # Separate successful and failed URLs
        successful = [r for r in all_results if r["status"] == "success"]
        failed = [r for r in all_results if r["status"] == "failed"]
        
        logger.info(f"Custom JS rendering completed: {len(successful)} successful, {len(failed)} failed")
        
        return all_results

