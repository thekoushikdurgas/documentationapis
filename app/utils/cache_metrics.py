"""Cache performance metrics tracking."""

from collections import defaultdict
from functools import lru_cache
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheMetrics:
    """Track cache performance metrics."""
    
    def __init__(self, enabled: bool = True):
        """Initialize cache metrics.
        
        Args:
            enabled: Whether metrics collection is enabled
        """
        self.enabled = enabled and getattr(settings, 'CACHE_METRICS_ENABLED', True)
        self.hits = defaultdict(int)
        self.misses = defaultdict(int)
        self.refresh_count = defaultdict(int)
        self.refresh_failures = defaultdict(int)
        self.response_times = defaultdict(list)  # endpoint -> [times]
    
    def record_cache_hit(self, endpoint: str) -> None:
        """Record cache hit.
        
        Args:
            endpoint: Endpoint name (e.g., "GET /docs")
        """
        if not self.enabled:
            return
        self.hits[endpoint] += 1
    
    def record_cache_miss(self, endpoint: str) -> None:
        """Record cache miss.
        
        Args:
            endpoint: Endpoint name
        """
        if not self.enabled:
            return
        self.misses[endpoint] += 1
    
    def record_refresh(self, endpoint: str, success: bool = True) -> None:
        """Record cache refresh attempt.
        
        Args:
            endpoint: Endpoint name
            success: Whether refresh succeeded
        """
        if not self.enabled:
            return
        if success:
            self.refresh_count[endpoint] += 1
        else:
            self.refresh_failures[endpoint] += 1
    
    def record_response_time(self, endpoint: str, time_ms: float, cached: bool) -> None:
        """Record endpoint response time.
        
        Args:
            endpoint: Endpoint name
            time_ms: Response time in milliseconds
            cached: Whether response was from cache
        """
        if not self.enabled:
            return
        # Keep last 1000 response times per endpoint
        if len(self.response_times[endpoint]) >= 1000:
            self.response_times[endpoint].pop(0)
        self.response_times[endpoint].append({
            "time_ms": time_ms,
            "cached": cached
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "endpoints": {}
        }
        
        all_endpoints = set(self.hits.keys()) | set(self.misses.keys())
        
        for endpoint in all_endpoints:
            hits = self.hits[endpoint]
            misses = self.misses[endpoint]
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            # Calculate average response times
            times = self.response_times[endpoint]
            cached_times = [t["time_ms"] for t in times if t["cached"]]
            uncached_times = [t["time_ms"] for t in times if not t["cached"]]
            
            avg_cached = sum(cached_times) / len(cached_times) if cached_times else 0
            avg_uncached = sum(uncached_times) / len(uncached_times) if uncached_times else 0
            
            stats["endpoints"][endpoint] = {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate_percent": round(hit_rate, 2),
                "refresh_count": self.refresh_count[endpoint],
                "refresh_failures": self.refresh_failures[endpoint],
                "avg_response_time_ms": {
                    "cached": round(avg_cached, 2),
                    "uncached": round(avg_uncached, 2)
                }
            }
        
        return stats


# Global metrics instance
_metrics_instance: Optional[CacheMetrics] = None


@lru_cache()
def get_cache_metrics() -> CacheMetrics:
    """Get or create cache metrics instance.
    
    Returns:
        CacheMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CacheMetrics()
    return _metrics_instance

