"""
Custom exceptions for the URL to HTML converter library.
"""


class FetchError(Exception):
    """Base exception for all fetch-related errors."""
    
    def __init__(self, message: str = "", url: str = ""):
        """
        Initialize fetch error.
        
        Args:
            message: Error message
            url: URL that caused the error (optional)
        """
        self.message = message
        self.url = url
        super().__init__(self.message)
    
    def __str__(self):
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message


class BlockedError(FetchError):
    """Raised when a request is blocked (4xx, 5xx status codes)."""
    
    def __init__(self, message: str = "", url: str = "", status_code: int = 0):
        """
        Initialize blocked error.
        
        Args:
            message: Error message
            url: URL that was blocked
            status_code: HTTP status code that indicated blocking
        """
        self.status_code = status_code
        super().__init__(message, url)
    
    def __str__(self):
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} (Status: {self.status_code})"
        return base_msg


class SkeletonContentError(FetchError):
    """Raised when content appears to be skeleton/placeholder content."""
    
    def __init__(self, message: str = "", url: str = "", reason: str = ""):
        """
        Initialize skeleton content error.
        
        Args:
            message: Error message
            url: URL that returned skeleton content
            reason: Reason why content was identified as skeleton
        """
        self.reason = reason
        super().__init__(message, url)
    
    def __str__(self):
        base_msg = super().__str__()
        if self.reason:
            return f"{base_msg} (Reason: {self.reason})"
        return base_msg


class TimeoutError(FetchError):
    """Raised when a request times out."""
    
    def __init__(self, message: str = "", url: str = "", timeout: float = 0):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            url: URL that timed out
            timeout: Timeout value in seconds
        """
        self.timeout = timeout
        super().__init__(message, url)
    
    def __str__(self):
        base_msg = super().__str__()
        if self.timeout:
            return f"{base_msg} (Timeout: {self.timeout}s)"
        return base_msg


class InvalidURLError(FetchError):
    """Raised when an invalid URL is provided."""
    
    def __init__(self, message: str = "", url: str = ""):
        """
        Initialize invalid URL error.
        
        Args:
            message: Error message
            url: Invalid URL that was provided
        """
        super().__init__(message, url)


class JSRenderError(FetchError):
    """Raised when JS rendering via external API fails."""
    
    def __init__(self, message: str = "", url: str = "", api_endpoint: str = ""):
        """
        Initialize JS render error.
        
        Args:
            message: Error message
            url: URL that failed to render
            api_endpoint: API endpoint that was called (optional)
        """
        self.api_endpoint = api_endpoint
        super().__init__(message, url)
    
    def __str__(self):
        base_msg = super().__str__()
        if self.api_endpoint:
            return f"{base_msg} (API: {self.api_endpoint})"
        return base_msg

