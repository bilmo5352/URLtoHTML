"""
Result aggregation and summary generation.
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ResultAggregator:
    """Aggregates results from all processing phases."""
    
    def __init__(self):
        """Initialize the result aggregator."""
        self.results: List[Dict[str, any]] = []
    
    def add_result(
        self,
        url: str,
        html: Optional[str],
        method: Optional[str],
        status: str,
        error: Optional[str] = None
    ):
        """
        Add a result to the aggregator.
        
        Args:
            url: URL that was processed
            html: HTML content (None if failed)
            method: Method used (static, xhr, custom_js, decodo)
            status: Status (success or failed)
            error: Error message if failed
        """
        self.results.append({
            "url": url,
            "html": html,
            "method": method,
            "status": status,
            "error": error
        })
    
    def add_results(self, results: List[Dict[str, any]]):
        """
        Add multiple results at once.
        
        Args:
            results: List of result dictionaries
        """
        self.results.extend(results)
    
    def get_summary(self) -> Dict[str, any]:
        """
        Generate summary statistics.
        
        Returns:
            Summary dictionary with statistics
        """
        total = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "success")
        failed = total - successful
        
        # Count by method
        by_method = defaultdict(int)
        for r in self.results:
            if r["method"]:
                by_method[r["method"]] += 1
        
        # Count JS batches (approximate - count custom_js results)
        custom_js_count = by_method.get("custom_js", 0)
        js_batches = (custom_js_count + 19) // 20  # Round up division
        
        # Count Decodo fallback
        decodo_count = by_method.get("decodo", 0)
        
        return {
            "total": total,
            "success": successful,
            "failed": failed,
            "by_method": dict(by_method),
            "js_batches_processed": js_batches,
            "decodo_fallback_count": decodo_count
        }
    
    def get_results(self) -> List[Dict[str, any]]:
        """
        Get all results.
        
        Returns:
            List of result dictionaries
        """
        return self.results
    
    def get_final_result(self, total_time: float) -> Dict[str, any]:
        """
        Get final aggregated result with summary.
        
        Args:
            total_time: Total processing time in seconds
            
        Returns:
            Final result dictionary with results and summary
        """
        summary = self.get_summary()
        summary["total_time"] = total_time
        
        return {
            "results": self.results,
            "summary": summary
        }

