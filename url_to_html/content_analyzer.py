"""
Content analysis and detection for blocked or skeleton content.
"""

import logging
from bs4 import BeautifulSoup
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes HTML content to detect if it's blocked or skeleton content."""
    
    def __init__(
        self,
        min_content_length: int = 1000,
        min_text_length: int = 200,
        min_meaningful_elements: int = 5,
        text_to_markup_ratio: float = 0.001
    ):
        """
        Initialize the content analyzer.
        
        Args:
            min_content_length: Minimum total content length in bytes
            min_text_length: Minimum text content length in characters
            min_meaningful_elements: Minimum number of meaningful elements (text, images, links)
            text_to_markup_ratio: Minimum ratio of text to HTML markup
        """
        self.min_content_length = min_content_length
        self.min_text_length = min_text_length
        self.min_meaningful_elements = min_meaningful_elements
        self.text_to_markup_ratio = text_to_markup_ratio
    
    def is_blocked(self, status_code: int) -> bool:
        """
        Check if response is blocked based on status code.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            True if status code indicates blocking
        """
        # 4xx and 5xx indicate blocking or errors
        if 400 <= status_code < 600:
            logger.debug(f"Status code {status_code} indicates blocking")
            return True
        return False
    
    def is_skeleton_content(
        self,
        html_content: str,
        status_code: int = 200
    ) -> Tuple[bool, str]:
        """
        Analyze HTML content to determine if it's skeleton/placeholder content.
        
        Args:
            html_content: HTML content to analyze
            status_code: HTTP status code (default: 200)
            
        Returns:
            Tuple of (is_skeleton: bool, reason: str)
        """
        if not html_content:
            return True, "Empty content"
        
        # Check content length
        content_length = len(html_content)
        if content_length < self.min_content_length:
            logger.debug(f"Content length {content_length} below threshold {self.min_content_length}")
            return True, f"Content too short ({content_length} bytes)"
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            # If we can't parse, but content is long enough, assume it's valid
            if content_length >= self.min_content_length:
                return False, "Valid content (unparseable but sufficient length)"
            return True, f"Unparseable content: {e}"
        
        # Extract text content
        text_content = soup.get_text(separator=' ', strip=True)
        text_length = len(text_content)
        
        # Check text length
        if text_length < self.min_text_length:
            logger.debug(f"Text length {text_length} below threshold {self.min_text_length}")
            return True, f"Text content too short ({text_length} chars)"
        
        # Count meaningful elements
        meaningful_elements = (
            len(soup.find_all(['p', 'article', 'section', 'div'], string=True)) +
            len(soup.find_all('img', src=True)) +
            len(soup.find_all('a', href=True))
        )
        
        if meaningful_elements < self.min_meaningful_elements:
            logger.debug(f"Meaningful elements {meaningful_elements} below threshold {self.min_meaningful_elements}")
            return True, f"Too few meaningful elements ({meaningful_elements})"
        
        # Check text-to-markup ratio (be more lenient for large pages)
        markup_length = len(html_content) - text_length
        if markup_length > 0:
            ratio = text_length / markup_length
            
            # For large pages (>100KB), use a more lenient threshold
            # Modern web pages (especially e-commerce) have lots of markup
            effective_threshold = self.text_to_markup_ratio
            if content_length > 100000:  # 100KB
                effective_threshold = self.text_to_markup_ratio * 0.5  # Half the threshold for large pages
            
            if ratio < effective_threshold:
                # Only fail if ratio is very low AND content is small
                # Large pages with low ratio are often valid (e.g., Amazon, modern SPAs)
                if content_length < 50000:  # Only strict check for smaller pages
                    logger.debug(f"Text-to-markup ratio {ratio:.4f} below threshold {effective_threshold}")
                    return True, f"Low text-to-markup ratio ({ratio:.4f})"
                else:
                    # Large page with low ratio - likely valid, just log it
                    logger.debug(f"Large page with low text-to-markup ratio {ratio:.4f}, but content size suggests it's valid")
        
        # Check for common skeleton indicators
        skeleton_indicators = [
            'loading',
            'skeleton',
            'placeholder',
            'spinner',
            'shimmer',
            'pulse'
        ]
        
        html_lower = html_content.lower()
        skeleton_count = sum(1 for indicator in skeleton_indicators if indicator in html_lower)
        
        # If many skeleton indicators and low content, likely skeleton
        if skeleton_count >= 3 and text_length < self.min_text_length * 2:
            logger.debug(f"Found {skeleton_count} skeleton indicators with low content")
            return True, f"Multiple skeleton indicators ({skeleton_count})"
        
        # Check for minimal content patterns (lots of divs, little text)
        divs = soup.find_all('div')
        if len(divs) > 20 and text_length < self.min_text_length * 3:
            logger.debug(f"Many divs ({len(divs)}) but little text ({text_length})")
            return True, f"Layout-heavy, content-light ({len(divs)} divs, {text_length} chars)"
        
        return False, "Valid content"
    
    def should_fallback(
        self,
        html_content: Optional[str],
        status_code: int
    ) -> Tuple[bool, str]:
        """
        Determine if we should fallback to next method.
        
        Args:
            html_content: HTML content (None if request failed)
            status_code: HTTP status code
            
        Returns:
            Tuple of (should_fallback: bool, reason: str)
        """
        # Check if blocked
        if self.is_blocked(status_code):
            return True, f"Request blocked (status {status_code})"
        
        # If no content, fallback
        if html_content is None:
            return True, "No content received"
        
        # Check if skeleton
        is_skeleton, reason = self.is_skeleton_content(html_content, status_code)
        if is_skeleton:
            return True, f"Skeleton content: {reason}"
        
        return False, "Content is valid"

