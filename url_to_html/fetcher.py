"""
Main fetcher with three-tier fallback strategy.
"""

import logging
import os
from urllib.parse import urlparse, quote
from typing import Optional, Dict, Any
from .static_fetcher import StaticFetcher
from .xhr_fetcher import XHRFetcher
from .js_renderer import JSrend
from .content_analyzer import ContentAnalyzer
from .exceptions import FetchError, JSRenderError, TimeoutError

logger = logging.getLogger(__name__)


def _save_html_to_file(html_content: str, url: str, method: str, output_dir: str = "outputs") -> str:
    """
    Save HTML content to a file for verification.
    
    Args:
        html_content: HTML content to save
        url: Original URL
        method: Method used (static, xhr, js)
        output_dir: Directory to save files in
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a safe filename from URL
    parsed = urlparse(url)
    domain = parsed.netloc.replace('.', '_')
    path = parsed.path.replace('/', '_').strip('_') or 'index'
    query = parsed.query.replace('&', '_').replace('=', '_') if parsed.query else ''
    
    # Limit filename length
    filename_base = f"{domain}_{path}"
    if query:
        filename_base += f"_{query[:50]}"
    filename_base = filename_base[:100]  # Limit total length
    
    # Add method and timestamp
    import time
    timestamp = int(time.time())
    filename = f"{method}_{filename_base}_{timestamp}.html"
    
    # Make filename safe
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
    
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved {method} output to: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to save {method} output: {e}")
        return ""


class FetcherConfig:
    """Configuration for the fetcher."""
    
    def __init__(
        self,
        # Static fetcher config
        static_timeout: int = 30,
        static_headers: Optional[Dict[str, str]] = None,
        
        # XHR fetcher config
        xhr_timeout: int = 30,
        xhr_headers: Optional[Dict[str, str]] = None,
        
        # JS renderer config (Decodo)
        js_api_endpoint: Optional[str] = None,
        js_api_key: Optional[str] = None,
        js_timeout: int = 180,
        js_headers: Optional[Dict[str, str]] = None,
        js_username: Optional[str] = None,
        js_password: Optional[str] = None,
        js_headless_mode: str = "html",
        js_location: Optional[str] = None,
        js_language: Optional[str] = None,
        
        # Content analyzer config
        min_content_length: int = 1000,
        min_text_length: int = 200,
        min_meaningful_elements: int = 5,
        text_to_markup_ratio: float = 0.001,
        
        # General config
        enable_logging: bool = True,
        log_level: int = logging.INFO,
        save_outputs: bool = True,
        output_dir: str = "outputs"
    ):
        """Initialize fetcher configuration."""
        self.static_timeout = static_timeout
        self.static_headers = static_headers or {}
        self.xhr_timeout = xhr_timeout
        self.xhr_headers = xhr_headers or {}
        self.js_api_endpoint = js_api_endpoint
        self.js_api_key = js_api_key
        self.js_timeout = js_timeout
        self.js_headers = js_headers or {}
        self.js_username = js_username
        self.js_password = js_password
        self.js_headless_mode = js_headless_mode
        self.js_location = js_location
        self.js_language = js_language
        self.min_content_length = min_content_length
        self.min_text_length = min_text_length
        self.min_meaningful_elements = min_meaningful_elements
        self.text_to_markup_ratio = text_to_markup_ratio
        self.enable_logging = enable_logging
        self.log_level = log_level
        self.save_outputs = save_outputs
        self.output_dir = output_dir


def fetch_html(
    url: str,
    config: Optional[FetcherConfig] = None,
    **kwargs
) -> str:
    """
    Fetch HTML content from URL using progressive fallback strategy.
    
    Strategy:
    1. Try static HTTP GET request
    2. If blocked or skeleton content, try XHR/API endpoints
    3. If still fails, use JS rendering via external API
    
    Args:
        url: URL to fetch
        config: FetcherConfig instance (optional)
        **kwargs: Additional configuration options (merged with config)
        
    Returns:
        HTML content as string
        
    Raises:
        FetchError: If all methods fail
    """
    # Setup logging if enabled
    if config and config.enable_logging:
        logging.basicConfig(
            level=config.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Create config from kwargs if not provided
    if config is None:
        config = FetcherConfig(**kwargs)
    else:
        # Merge kwargs into config
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Initialize components
    static_fetcher = StaticFetcher(
        timeout=config.static_timeout,
        headers=config.static_headers
    )
    
    xhr_fetcher = XHRFetcher(
        timeout=config.xhr_timeout,
        headers=config.xhr_headers
    )
    
    content_analyzer = ContentAnalyzer(
        min_content_length=config.min_content_length,
        min_text_length=config.min_text_length,
        min_meaningful_elements=config.min_meaningful_elements,
        text_to_markup_ratio=config.text_to_markup_ratio
    )
    
    logger.info(f"Starting fetch for URL: {url}")
    
    # Tier 1: Static Fetch
    try:
        logger.info("Tier 1: Attempting static fetch")
        html_content, status_code = static_fetcher.fetch(url)
        
        if html_content is not None:
            # Save static fetch output for verification
            if config.save_outputs:
                _save_html_to_file(html_content, url, "static", config.output_dir)
            
            should_fallback, reason = content_analyzer.should_fallback(
                html_content, status_code
            )
            
            if not should_fallback:
                logger.info("Static fetch successful, content is valid")
                return html_content
            else:
                logger.info(f"Static fetch returned insufficient content: {reason}")
        else:
            logger.info("Static fetch returned no content")
    
    except (TimeoutError, FetchError) as e:
        logger.warning(f"Static fetch failed: {e}")
    except Exception as e:
        logger.warning(f"Static fetch unexpected error: {e}")
    
    # Tier 2: XHR Fetch
    try:
        logger.info("Tier 2: Attempting XHR fetch")
        html_content, status_code = xhr_fetcher.fetch(url)
        
        if html_content is not None:
            # Save XHR fetch output for verification
            if config.save_outputs:
                _save_html_to_file(html_content, url, "xhr", config.output_dir)
            
            should_fallback, reason = content_analyzer.should_fallback(
                html_content, status_code
            )
            
            if not should_fallback:
                logger.info("XHR fetch successful, content is valid")
                return html_content
            else:
                logger.info(f"XHR fetch returned insufficient content: {reason}")
        else:
            logger.info("XHR fetch returned no content")
    
    except Exception as e:
        logger.warning(f"XHR fetch failed: {e}")
    
    # Tier 3: JS Rendering
    try:
        logger.info("Tier 3: Attempting JS rendering")
        html_content = JSrend(
            url,
            api_endpoint=config.js_api_endpoint,
            api_key=config.js_api_key,
            timeout=config.js_timeout,
            headers=config.js_headers,
            username=config.js_username,
            password=config.js_password,
            headless_mode=config.js_headless_mode,
            location=config.js_location,
            language=config.js_language
        )
        
        if html_content:
            # Save JS rendering output for verification
            if config.save_outputs:
                _save_html_to_file(html_content, url, "js", config.output_dir)
            
            logger.info(f"JS rendering successful: {len(html_content)} bytes")
            return html_content
        else:
            logger.warning("JS rendering returned empty content")
    
    except JSRenderError as e:
        # If JS rendering is required but not configured, stop here
        logger.error(f"JS rendering failed: {e}")
        print(f"\nJS rendering required for: {url}")
        print("Please configure js_api_endpoint in FetcherConfig to enable JS rendering.")
        raise  # Re-raise to stop execution
    except Exception as e:
        logger.error(f"JS rendering unexpected error: {e}")
    
    # All methods failed
    error_msg = (
        f"All fetch methods failed for URL: {url}. "
        "Tried: static fetch → XHR fetch → JS rendering"
    )
    logger.error(error_msg)
    raise FetchError(error_msg)

