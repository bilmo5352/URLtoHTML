"""
XHR/API fetch implementation for alternative endpoints.
"""

import logging
import requests
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class XHRFetcher:
    """Attempts to fetch content via XHR/API endpoints."""
    
    def __init__(
        self,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the XHR fetcher.
        
        Args:
            timeout: Request timeout in seconds
            headers: Custom headers to include in requests
        """
        self.timeout = timeout
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': '',
        }
        if headers:
            self.default_headers.update(headers)
    
    def _generate_api_endpoints(self, url: str) -> List[str]:
        """
        Generate potential API endpoints based on the URL.
        
        Args:
            url: Original URL
            
        Returns:
            List of potential API endpoint URLs
        """
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path.rstrip('/')
        
        endpoints = []
        
        # Common API patterns
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
        
        # Try JSON endpoint
        if path:
            endpoints.append(urljoin(base_url, path + '.json'))
        
        # Try with query parameters preserved
        if parsed.query:
            for pattern in api_patterns[:3]:  # Limit to avoid too many URLs
                endpoints.append(urljoin(base_url, pattern + '?' + parsed.query))
        
        return endpoints
    
    def fetch(self, url: str) -> Tuple[Optional[str], int]:
        """
        Attempt to fetch content via XHR/API endpoints.
        
        Args:
            url: Original URL to derive API endpoints from
            
        Returns:
            Tuple of (html_content: Optional[str], status_code: int)
        """
        logger.info(f"Attempting XHR fetch for: {url}")
        
        # Set referer to original URL
        headers = self.default_headers.copy()
        headers['Referer'] = url
        
        # First, try the original URL with XHR headers
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                try:
                    content = response.text
                    logger.info(f"XHR fetch successful (original URL): {len(content)} bytes")
                    return content, response.status_code
                except UnicodeDecodeError:
                    response.encoding = response.apparent_encoding or 'utf-8'
                    content = response.text
                    logger.info(f"XHR fetch successful (original URL): {len(content)} bytes")
                    return content, response.status_code
        except Exception as e:
            logger.debug(f"XHR fetch failed for original URL: {e}")
        
        # Try alternative API endpoints
        api_endpoints = self._generate_api_endpoints(url)
        logger.debug(f"Trying {len(api_endpoints)} alternative endpoints")
        
        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying XHR endpoint: {endpoint}")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    try:
                        content = response.text
                        # If it's JSON, try to extract HTML or return as-is
                        if response.headers.get('Content-Type', '').startswith('application/json'):
                            # JSON response - might contain HTML or data
                            # For now, return as text (could be enhanced to parse JSON)
                            logger.info(f"XHR fetch successful (JSON endpoint): {len(content)} bytes")
                            return content, response.status_code
                        else:
                            logger.info(f"XHR fetch successful (endpoint): {len(content)} bytes")
                            return content, response.status_code
                    except UnicodeDecodeError:
                        response.encoding = response.apparent_encoding or 'utf-8'
                        content = response.text
                        logger.info(f"XHR fetch successful (endpoint): {len(content)} bytes")
                        return content, response.status_code
                        
            except Exception as e:
                logger.debug(f"XHR fetch failed for endpoint {endpoint}: {e}")
                continue
        
        logger.warning(f"XHR fetch failed for all endpoints: {url}")
        return None, 0

