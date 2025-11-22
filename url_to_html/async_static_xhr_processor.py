"""
Async processor for static and XHR fetches with high concurrency.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from .content_analyzer import ContentAnalyzer
from .exceptions import TimeoutError, InvalidURLError

logger = logging.getLogger(__name__)


class AsyncStaticXHRProcessor:
    """High-concurrency async processor for static and XHR fetches."""
    
    def __init__(
        self,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        max_concurrent: int = 50
    ):
        """
        Initialize the async processor.
        
        Args:
            timeout: Request timeout in seconds
            headers: Custom headers to include in requests
            max_concurrent: Maximum concurrent requests
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        if headers:
            self.default_headers.update(headers)
        
        self.content_analyzer = ContentAnalyzer()
    
    async def _fetch_static(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Tuple[Optional[str], int]:
        """Fetch URL using static HTTP GET."""
        try:
            async with session.get(url, headers=self.default_headers) as response:
                status_code = response.status
                
                # Try to decode content
                try:
                    content = await response.text()
                except Exception:
                    content = await response.read()
                    try:
                        content = content.decode('utf-8')
                    except:
                        content = content.decode('utf-8', errors='ignore')
                
                logger.debug(f"Static fetch for {url}: {status_code}, {len(content)} bytes")
                return content, status_code
                
        except asyncio.TimeoutError:
            logger.warning(f"Static fetch timeout for: {url}")
            return None, 0
        except aiohttp.InvalidURL:
            logger.error(f"Invalid URL: {url}")
            return None, 0
        except Exception as e:
            logger.warning(f"Static fetch failed for {url}: {e}")
            return None, 0
    
    def _generate_api_endpoints(self, url: str) -> List[str]:
        """Generate potential API endpoints based on the URL."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path.rstrip('/')
        
        endpoints = []
        api_patterns = [
            '/api' + path,
            '/api/v1' + path,
            '/api/v2' + path,
            '/api/data' + path,
            path + '/data',
            path + '/api',
            '/data' + path,
        ]
        
        for pattern in api_patterns:
            endpoints.append(urljoin(base_url, pattern))
        
        if path:
            endpoints.append(urljoin(base_url, path + '.json'))
        
        if parsed.query:
            for pattern in api_patterns[:3]:
                endpoints.append(urljoin(base_url, pattern + '?' + parsed.query))
        
        return endpoints
    
    async def _fetch_xhr(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Tuple[Optional[str], int]:
        """Fetch URL using XHR/API endpoints."""
        xhr_headers = self.default_headers.copy()
        xhr_headers.update({
            'Accept': 'application/json, text/html, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': url,
        })
        
        # Try original URL with XHR headers
        try:
            async with session.get(url, headers=xhr_headers) as response:
                if response.status == 200:
                    try:
                        content = await response.text()
                        logger.debug(f"XHR fetch successful (original): {url}")
                        return content, response.status
                    except Exception:
                        content = await response.read()
                        try:
                            content = content.decode('utf-8')
                        except:
                            content = content.decode('utf-8', errors='ignore')
                        return content, response.status
        except Exception as e:
            logger.debug(f"XHR fetch failed for original URL {url}: {e}")
        
        # Try alternative endpoints
        api_endpoints = self._generate_api_endpoints(url)
        for endpoint in api_endpoints:
            try:
                async with session.get(endpoint, headers=xhr_headers) as response:
                    if response.status == 200:
                        try:
                            content = await response.text()
                            logger.debug(f"XHR fetch successful (endpoint): {endpoint}")
                            return content, response.status
                        except Exception:
                            content = await response.read()
                            try:
                                content = content.decode('utf-8')
                            except:
                                content = content.decode('utf-8', errors='ignore')
                            return content, response.status
            except Exception:
                continue
        
        logger.debug(f"XHR fetch failed for all endpoints: {url}")
        return None, 0
    
    async def _process_single_url(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Dict[str, any]:
        """
        Process a single URL through static and XHR fetches.
        
        Returns:
            {
                "url": str,
                "html": Optional[str],
                "method": "static" | "xhr" | None,
                "needs_js": bool,
                "error": Optional[str]
            }
        """
        # Try static fetch first
        html_content, status_code = await self._fetch_static(session, url)
        
        if html_content is not None:
            should_fallback, reason = self.content_analyzer.should_fallback(
                html_content, status_code
            )
            
            if not should_fallback:
                logger.debug(f"Static fetch successful for {url}")
                return {
                    "url": url,
                    "html": html_content,
                    "method": "static",
                    "needs_js": False,
                    "error": None
                }
            else:
                logger.debug(f"Static fetch returned insufficient content for {url}: {reason}")
        
        # Try XHR fetch
        html_content, status_code = await self._fetch_xhr(session, url)
        
        if html_content is not None:
            should_fallback, reason = self.content_analyzer.should_fallback(
                html_content, status_code
            )
            
            if not should_fallback:
                logger.debug(f"XHR fetch successful for {url}")
                return {
                    "url": url,
                    "html": html_content,
                    "method": "xhr",
                    "needs_js": False,
                    "error": None
                }
            else:
                logger.debug(f"XHR fetch returned insufficient content for {url}: {reason}")
        
        # Both failed, needs JS rendering
        logger.debug(f"Both static and XHR failed for {url}, needs JS rendering")
        return {
            "url": url,
            "html": None,
            "method": None,
            "needs_js": True,
            "error": "Static and XHR fetches failed or returned skeleton content"
        }
    
    async def process_batch(
        self,
        urls: List[str]
    ) -> List[Dict[str, any]]:
        """
        Process a batch of URLs with high concurrency.
        
        Args:
            urls: List of URLs to process
            
        Returns:
            List of result dictionaries
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(session: aiohttp.ClientSession, url: str):
            async with semaphore:
                return await self._process_single_url(session, url)
        
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector,
            headers=self.default_headers
        ) as session:
            tasks = [process_with_semaphore(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {urls[i]}: {result}")
                    processed_results.append({
                        "url": urls[i],
                        "html": None,
                        "method": None,
                        "needs_js": True,
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            return processed_results

