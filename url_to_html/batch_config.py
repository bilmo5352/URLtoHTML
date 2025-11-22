"""
Configuration for batch processing.
"""

from typing import Optional, Dict


class BatchFetcherConfig:
    """Configuration for batch URL fetching."""
    
    def __init__(
        self,
        # Static/XHR processing
        static_xhr_concurrency: int = 50,
        static_xhr_timeout: int = 30,
        static_xhr_headers: Optional[Dict[str, str]] = None,
        
        # Custom JS Service
        custom_js_api_url: str = "https://chromeworkers-copy-production.up.railway.app/render",
        custom_js_batch_size: int = 20,
        custom_js_cooldown_seconds: int = 120,  # 2 minutes
        custom_js_timeout: int = 300,  # 5 minutes for batch
        
        # Decodo (fallback only)
        decodo_enabled: bool = True,
        decodo_max_concurrent: int = 3,
        decodo_timeout: int = 180,
        decodo_headless_mode: str = "html",
        decodo_location: Optional[str] = None,
        decodo_language: Optional[str] = None,
        
        # Content analyzer
        min_content_length: int = 1000,
        min_text_length: int = 200,
        min_meaningful_elements: int = 5,
        text_to_markup_ratio: float = 0.001,
        
        # General
        save_outputs: bool = True,
        output_dir: str = "outputs",
        enable_logging: bool = True
    ):
        """
        Initialize batch fetcher configuration.
        
        Args:
            static_xhr_concurrency: Max concurrent static/XHR requests
            static_xhr_timeout: Timeout for static/XHR requests
            static_xhr_headers: Custom headers for static/XHR
            
            custom_js_api_url: Custom JS rendering API endpoint
            custom_js_batch_size: URLs per batch (default: 20)
            custom_js_cooldown_seconds: Cooldown between batches (default: 120)
            custom_js_timeout: Timeout for batch requests
            
            decodo_enabled: Whether to use Decodo as fallback
            decodo_max_concurrent: Max concurrent Decodo requests (default: 3)
            decodo_timeout: Timeout for Decodo requests
            decodo_headless_mode: Decodo rendering mode
            decodo_location: Decodo geographic location
            decodo_language: Decodo language locale
            
            min_content_length: Minimum content length threshold
            min_text_length: Minimum text length threshold
            min_meaningful_elements: Minimum meaningful elements
            text_to_markup_ratio: Text to markup ratio threshold
            
            save_outputs: Whether to save HTML outputs
            output_dir: Directory for saved outputs
            enable_logging: Whether to enable logging
        """
        # Static/XHR
        self.static_xhr_concurrency = static_xhr_concurrency
        self.static_xhr_timeout = static_xhr_timeout
        self.static_xhr_headers = static_xhr_headers or {}
        
        # Custom JS Service
        self.custom_js_api_url = custom_js_api_url
        self.custom_js_batch_size = custom_js_batch_size
        self.custom_js_cooldown_seconds = custom_js_cooldown_seconds
        self.custom_js_timeout = custom_js_timeout
        
        # Decodo
        self.decodo_enabled = decodo_enabled
        self.decodo_max_concurrent = decodo_max_concurrent
        self.decodo_timeout = decodo_timeout
        self.decodo_headless_mode = decodo_headless_mode
        self.decodo_location = decodo_location
        self.decodo_language = decodo_language
        
        # Content analyzer
        self.min_content_length = min_content_length
        self.min_text_length = min_text_length
        self.min_meaningful_elements = min_meaningful_elements
        self.text_to_markup_ratio = text_to_markup_ratio
        
        # General
        self.save_outputs = save_outputs
        self.output_dir = output_dir
        self.enable_logging = enable_logging

