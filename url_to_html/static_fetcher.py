"""
Static HTTP fetch implementation.
"""

import logging
import requests
from typing import Optional, Dict, Any, Tuple
from .exceptions import BlockedError, TimeoutError, InvalidURLError

logger = logging.getLogger(__name__)


class StaticFetcher:
    """Fetches HTML content using direct HTTP GET requests."""
    
    def __init__(
        self,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        allow_redirects: bool = True
    ):
        """
        Initialize the static fetcher.
        
        Args:
            timeout: Request timeout in seconds
            headers: Custom headers to include in requests
            allow_redirects: Whether to follow redirects
        """
        self.timeout = timeout
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
        self.allow_redirects = allow_redirects
    
    def fetch(self, url: str) -> Tuple[Optional[str], int]:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content: Optional[str], status_code: int)
            
        Raises:
            InvalidURLError: If URL is invalid
            TimeoutError: If request times out
        """
        try:
            logger.info(f"Attempting static fetch for: {url}")
            response = requests.get(
                url,
                headers=self.default_headers,
                timeout=self.timeout,
                allow_redirects=self.allow_redirects
            )
            
            status_code = response.status_code
            logger.debug(f"Static fetch status code: {status_code}")
            
            # Try to decode content
            try:
                content = response.text
            except UnicodeDecodeError:
                # Try with different encoding
                response.encoding = response.apparent_encoding or 'utf-8'
                content = response.text
            
            logger.info(f"Static fetch successful: {len(content)} bytes, status {status_code}")
            return content, status_code
            
        except requests.exceptions.Timeout:
            logger.warning(f"Static fetch timeout for: {url}")
            raise TimeoutError(f"Request to {url} timed out after {self.timeout}s")
        
        except requests.exceptions.InvalidURL:
            logger.error(f"Invalid URL: {url}")
            raise InvalidURLError(f"Invalid URL: {url}")
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Static fetch failed for {url}: {e}")
            # Return None to indicate failure, but don't raise exception
            # Let the fallback mechanism handle it
            return None, 0

