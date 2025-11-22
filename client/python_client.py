"""
Python client for URL to HTML Converter API.

Simple, easy-to-use client for fetching HTML content from URLs.
"""

import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class BatchRequest:
    """Request configuration for batch URL fetching."""
    
    urls: List[str]
    static_xhr_concurrency: Optional[int] = None
    static_xhr_timeout: Optional[int] = None
    custom_js_service_endpoints: Optional[List[str]] = None
    custom_js_batch_size: Optional[int] = None
    custom_js_cooldown_seconds: Optional[int] = None
    custom_js_timeout: Optional[int] = None
    decodo_enabled: Optional[bool] = None
    decodo_timeout: Optional[int] = None
    min_content_length: Optional[int] = None
    min_text_length: Optional[int] = None
    save_outputs: Optional[bool] = None
    enable_logging: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request format."""
        data = {"urls": self.urls}
        
        config = {}
        if self.static_xhr_concurrency is not None:
            config["static_xhr_concurrency"] = self.static_xhr_concurrency
        if self.static_xhr_timeout is not None:
            config["static_xhr_timeout"] = self.static_xhr_timeout
        if self.custom_js_service_endpoints is not None:
            config["custom_js_service_endpoints"] = self.custom_js_service_endpoints
        if self.custom_js_batch_size is not None:
            config["custom_js_batch_size"] = self.custom_js_batch_size
        if self.custom_js_cooldown_seconds is not None:
            config["custom_js_cooldown_seconds"] = self.custom_js_cooldown_seconds
        if self.custom_js_timeout is not None:
            config["custom_js_timeout"] = self.custom_js_timeout
        if self.decodo_enabled is not None:
            config["decodo_enabled"] = self.decodo_enabled
        if self.decodo_timeout is not None:
            config["decodo_timeout"] = self.decodo_timeout
        if self.min_content_length is not None:
            config["min_content_length"] = self.min_content_length
        if self.min_text_length is not None:
            config["min_text_length"] = self.min_text_length
        if self.save_outputs is not None:
            config["save_outputs"] = self.save_outputs
        if self.enable_logging is not None:
            config["enable_logging"] = self.enable_logging
        
        if config:
            data["config"] = config
        
        return data


@dataclass
class URLResult:
    """Result for a single URL."""
    
    url: str
    html: Optional[str]
    method: Optional[str]
    status: str
    error: Optional[str]
    
    @property
    def is_success(self) -> bool:
        """Check if the fetch was successful."""
        return self.status == "success" and self.html is not None
    
    @property
    def is_failed(self) -> bool:
        """Check if the fetch failed."""
        return self.status == "failed"


@dataclass
class BatchSummary:
    """Summary statistics for batch processing."""
    
    total: int
    success: int
    failed: int
    by_method: Dict[str, int]
    total_time: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.success / self.total) * 100


@dataclass
class BatchResponse:
    """Response from batch URL fetching."""
    
    results: List[URLResult]
    summary: BatchSummary
    success: bool
    
    def get_successful(self) -> List[URLResult]:
        """Get only successful results."""
        return [r for r in self.results if r.is_success]
    
    def get_failed(self) -> List[URLResult]:
        """Get only failed results."""
        return [r for r in self.results if r.is_failed]
    
    def get_by_method(self, method: str) -> List[URLResult]:
        """Get results by method (static, xhr, custom_js, decodo)."""
        return [r for r in self.results if r.method == method]


class URLToHTMLClient:
    """
    Client for URL to HTML Converter API.
    
    Simple, easy-to-use client for fetching HTML content from URLs.
    
    Example:
        ```python
        from client import URLToHTMLClient
        
        # Initialize client
        client = URLToHTMLClient(base_url="http://localhost:8000")
        
        # Fetch a batch of URLs
        urls = [
            "https://example.com/page1",
            "https://example.com/page2"
        ]
        
        response = client.fetch_batch(urls)
        
        # Check results
        print(f"Success: {response.summary.success}")
        print(f"Failed: {response.summary.failed}")
        
        # Get HTML for successful URLs
        for result in response.get_successful():
            print(f"{result.url}: {len(result.html)} bytes")
        ```
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 3600,  # 1 hour default for large batches
        verify_ssl: bool = True
    ):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API (default: "http://localhost:8000")
            timeout: Request timeout in seconds (default: 3600 for large batches)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health.
        
        Returns:
            Health status information
            
        Example:
            ```python
            health = client.health_check()
            print(health['status'])  # 'healthy'
            ```
        """
        response = self.session.get(
            f"{self.base_url}/health",
            timeout=10,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API information.
        
        Returns:
            API information including version and endpoints
            
        Example:
            ```python
            info = client.get_api_info()
            print(info['version'])  # '1.0.0'
            ```
        """
        response = self.session.get(
            f"{self.base_url}/",
            timeout=10,
            verify=self.verify_ssl
        )
        response.raise_for_status()
        return response.json()
    
    def fetch_batch(
        self,
        urls: List[str],
        static_xhr_concurrency: Optional[int] = None,
        custom_js_service_endpoints: Optional[List[str]] = None,
        custom_js_batch_size: Optional[int] = None,
        **kwargs
    ) -> BatchResponse:
        """
        Fetch HTML content for a batch of URLs.
        
        This is the main method for fetching HTML content. It uses a progressive
        fallback strategy:
        1. Static HTTP GET
        2. XHR/API fetch
        3. Custom JS rendering (multi-service parallel)
        4. Decodo fallback (for failed URLs)
        
        Args:
            urls: List of URLs to fetch (1-10000 URLs)
            static_xhr_concurrency: Max concurrent static/XHR requests (default: 100)
            custom_js_service_endpoints: List of custom JS rendering service endpoints
            custom_js_batch_size: URLs per batch for custom JS (default: 20)
            **kwargs: Additional configuration options:
                - static_xhr_timeout: Timeout for static/XHR requests
                - custom_js_cooldown_seconds: Cooldown between batches
                - custom_js_timeout: Timeout for custom JS batch requests
                - decodo_enabled: Whether to use Decodo as fallback
                - decodo_timeout: Timeout for Decodo requests
                - min_content_length: Minimum content length threshold
                - min_text_length: Minimum text length threshold
                - save_outputs: Whether to save HTML outputs to disk
                - enable_logging: Whether to enable detailed logging
        
        Returns:
            BatchResponse with results and summary
            
        Raises:
            requests.HTTPError: If the API request fails
            requests.RequestException: If there's a network error
            
        Example:
            ```python
            # Simple usage
            urls = ["https://example.com/page1", "https://example.com/page2"]
            response = client.fetch_batch(urls)
            
            # With custom configuration
            response = client.fetch_batch(
                urls,
                static_xhr_concurrency=200,
                custom_js_service_endpoints=[
                    "service1.com",
                    "service2.com",
                    "service3.com"
                ],
                custom_js_batch_size=20
            )
            
            # Check results
            print(f"Total: {response.summary.total}")
            print(f"Success: {response.summary.success}")
            print(f"Failed: {response.summary.failed}")
            print(f"Success Rate: {response.summary.success_rate:.2f}%")
            print(f"Time: {response.summary.total_time:.2f}s")
            
            # Get HTML content
            for result in response.get_successful():
                print(f"{result.url}: {len(result.html)} bytes via {result.method}")
            
            # Handle failures
            for result in response.get_failed():
                print(f"Failed {result.url}: {result.error}")
            ```
        """
        # Build request
        request = BatchRequest(
            urls=urls,
            static_xhr_concurrency=static_xhr_concurrency,
            custom_js_service_endpoints=custom_js_service_endpoints,
            custom_js_batch_size=custom_js_batch_size,
            **kwargs
        )
        
        # Make API request
        response = self.session.post(
            f"{self.base_url}/api/v1/fetch-batch",
            json=request.to_dict(),
            timeout=self.timeout,
            verify=self.verify_ssl,
            headers={"Content-Type": "application/json"}
        )
        
        # Handle errors
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            # Try to get error details from response
            try:
                error_data = response.json()
                error_msg = error_data.get("error", str(e))
                detail = error_data.get("detail", "")
                raise requests.HTTPError(
                    f"{error_msg}: {detail}" if detail else error_msg,
                    response=response
                )
            except (ValueError, KeyError):
                raise e
        
        # Parse response
        data = response.json()
        
        # Convert to response objects
        results = [
            URLResult(
                url=r["url"],
                html=r.get("html"),
                method=r.get("method"),
                status=r["status"],
                error=r.get("error")
            )
            for r in data["results"]
        ]
        
        summary = BatchSummary(
            total=data["summary"]["total"],
            success=data["summary"]["success"],
            failed=data["summary"]["failed"],
            by_method=data["summary"]["by_method"],
            total_time=data["summary"]["total_time"]
        )
        
        return BatchResponse(
            results=results,
            summary=summary,
            success=data["success"]
        )
    
    def fetch_single(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch HTML content for a single URL (convenience method).
        
        Args:
            url: URL to fetch
            **kwargs: Configuration options (same as fetch_batch)
        
        Returns:
            HTML content as string, or None if failed
            
        Example:
            ```python
            html = client.fetch_single("https://example.com")
            if html:
                print(f"Got {len(html)} bytes")
            ```
        """
        response = self.fetch_batch([url], **kwargs)
        if response.results and response.results[0].is_success:
            return response.results[0].html
        return None
    
    def close(self):
        """Close the session (cleanup)."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

