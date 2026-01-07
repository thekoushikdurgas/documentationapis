"""Request/response monitoring middleware."""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.cache_metrics import get_cache_metrics



class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor request/response performance."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log performance metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Check if response was cached (from cache metadata in response body)
        cached = False
        try:
            # Try to read response body to check cache status
            # Note: This is a simplified check - in production, you might want
            # to use response headers or a different mechanism
            if hasattr(response, 'body'):
                # Response might have cache metadata
                cached = False  # Default - will be updated by endpoint logic
        except Exception:
            pass
        
        # Record metrics
        endpoint = f"{request.method} {request.url.path}"
        metrics = get_cache_metrics()
        metrics.record_response_time(endpoint, duration_ms, cached)
        
        return response

