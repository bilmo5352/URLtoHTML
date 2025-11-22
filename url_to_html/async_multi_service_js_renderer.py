"""
Async multi-service JS renderer that distributes URLs across multiple services in parallel.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from .service_pool_manager import ServicePoolManager, ServiceInfo
from .exceptions import JSRenderError

logger = logging.getLogger(__name__)


class AsyncMultiServiceJSRenderer:
    """Multi-service batch processor for JS rendering with parallel service utilization."""
    
    def __init__(
        self,
        service_endpoints: List[str],
        batch_size: int = 20,
        cooldown_seconds: int = 120,
        timeout: int = 300
    ):
        """
        Initialize the multi-service JS renderer.
        
        Args:
            service_endpoints: List of service endpoint URLs
            batch_size: Number of URLs per batch (default: 20)
            cooldown_seconds: Cooldown period after each batch (default: 120)
            timeout: Request timeout in seconds
        """
        self.service_pool = ServicePoolManager(
            service_endpoints=service_endpoints,
            batch_size=batch_size,
            cooldown_seconds=cooldown_seconds
        )
        self.batch_size = batch_size
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def _process_batch_with_service(
        self,
        session: aiohttp.ClientSession,
        service: ServiceInfo,
        urls: List[str],
        batch_id: int
    ) -> List[Dict[str, any]]:
        """
        Process a batch of URLs using a specific service.
        
        Args:
            session: aiohttp session
            service: Service to use
            urls: List of URLs to process
            batch_id: Batch identifier for logging
            
        Returns:
            List of result dictionaries
        """
        logger.info(f"Processing batch {batch_id} with service {service.endpoint} ({len(urls)} URLs)")
        
        try:
            payload = {"urls": urls}
            
            async with session.post(
                service.endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Service {service.endpoint} returned status {response.status}: {error_text[:200]}")
                    await self.service_pool.mark_service_failed(service)
                    # Return failed results
                    return [
                        {
                            "url": url,
                            "html": None,
                            "status": "failed",
                            "error": f"Service returned status {response.status}: {error_text[:200]}"
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
                    logger.warning(f"Unexpected response format from service {service.endpoint}")
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
                logger.info(f"Batch {batch_id} completed on {service.endpoint}: {successful} successful, {failed} failed")
                
                # Mark service as in cooldown
                await self.service_pool.mark_service_cooldown(service)
                
                return results
                
        except asyncio.TimeoutError:
            logger.error(f"Batch {batch_id} timed out on service {service.endpoint}")
            await self.service_pool.mark_service_failed(service)
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
            logger.error(f"Batch {batch_id} failed on service {service.endpoint}: {e}")
            await self.service_pool.mark_service_failed(service)
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
        Process URLs by distributing them across all available services in parallel.
        
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
        
        logger.info(f"Processing {len(urls)} URLs in {len(batches)} batches across {self.service_pool.get_service_count()} services")
        
        all_results = []
        batch_queue = asyncio.Queue()
        
        # Add all batches to queue
        for batch_num, batch_urls in enumerate(batches, 1):
            await batch_queue.put((batch_num, batch_urls))
        
        async def process_batch_worker():
            """Worker coroutine that processes batches from queue."""
            while True:
                batch_num = None
                batch_urls = None
                try:
                    # Get batch from queue
                    try:
                        batch_num, batch_urls = await asyncio.wait_for(batch_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # Check if queue is empty
                        if batch_queue.empty():
                            break
                        continue
                    
                    # Wait for an available service
                    service = await self.service_pool.wait_for_available_service(timeout=300)
                    if not service:
                        logger.error(f"Timeout waiting for available service for batch {batch_num}")
                        # Add failed results
                        all_results.extend([
                            {
                                "url": url,
                                "html": None,
                                "status": "failed",
                                "error": "No available service (timeout)"
                            }
                            for url in batch_urls
                        ])
                        batch_queue.task_done()
                        continue
                    
                    # Mark service as processing
                    await self.service_pool.mark_service_processing(service)
                    
                    # Process batch
                    try:
                        async with aiohttp.ClientSession(timeout=self.timeout) as session:
                            batch_results = await self._process_batch_with_service(
                                session, service, batch_urls, batch_num
                            )
                            all_results.extend(batch_results)
                    finally:
                        batch_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"Error in batch worker: {e}")
                    if batch_num is not None and batch_urls is not None:
                        # Add failed results
                        all_results.extend([
                            {
                                "url": url,
                                "html": None,
                                "status": "failed",
                                "error": str(e)
                            }
                            for url in batch_urls
                        ])
                        batch_queue.task_done()
        
        # Start worker tasks (one per service for maximum parallelism)
        num_workers = min(len(batches), self.service_pool.get_service_count())
        workers = [asyncio.create_task(process_batch_worker()) for _ in range(num_workers)]
        
        # Wait for all batches to complete
        await batch_queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)
        
        # Separate successful and failed URLs
        successful = [r for r in all_results if r["status"] == "success"]
        failed = [r for r in all_results if r["status"] == "failed"]
        
        status_summary = await self.service_pool.get_status_summary()
        logger.info(f"Multi-service JS rendering completed: {len(successful)} successful, {len(failed)} failed")
        logger.info(f"Service status: {status_summary}")
        
        return all_results

