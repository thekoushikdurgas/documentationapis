"""MongoDB client for async database operations with optimized connection pooling."""

import asyncio
import time
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.utils.lambda_utils import IS_LAMBDA, safe_await_in_lambda
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global MongoDB client instance
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_database: Optional[AsyncIOMotorDatabase] = None

# Health check cache
_health_cache: Dict[str, Any] = {
    "status": None,
    "last_checked": None,
    "ttl": 30,  # seconds
    "stale_ttl": 60,  # seconds (2x TTL)
}


def _build_mongodb_uri() -> str:
    """Build MongoDB URI from configuration."""
    if settings.MONGODB_URI:
        return settings.MONGODB_URI
    
    # Build URI from components
    if settings.MONGODB_AUTH and settings.MONGODB_USER and settings.MONGODB_PASSWORD:
        auth = f"{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@"
    else:
        auth = ""
    
    host = settings.MONGODB_HOST or "localhost"
    port = settings.MONGODB_PORT or "27017"
    
    return f"mongodb://{auth}{host}:{port}"


async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance, creating connection if needed.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Raises:
        ConnectionError: If connection to MongoDB fails
    """
    global _mongodb_client, _mongodb_database
    
    if _mongodb_database is not None:
        return _mongodb_database
    
    # Build MongoDB URI
    mongodb_uri = _build_mongodb_uri()
    
    # Create client with optimized connection pool settings
    if _mongodb_client is None:
        _mongodb_client = AsyncIOMotorClient(
            mongodb_uri,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME_MS,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
        )
    
    # Get or create database
    db_name = settings.MONGODB_DB_NAME
    _mongodb_database = _mongodb_client[db_name]
    
    # Test connection
    try:
        await _mongodb_client.admin.command('ping')
        
        # Initialize health cache on successful connection
        _health_cache["status"] = True
        _health_cache["last_checked"] = time.time()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
        # Set health cache to unhealthy
        _health_cache["status"] = False
        _health_cache["last_checked"] = time.time()
        raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e
    
    return _mongodb_database


async def close_mongodb_connection() -> None:
    """Close MongoDB connection gracefully."""
    global _mongodb_client, _mongodb_database
    
    if _mongodb_client is not None:
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_database = None


def is_mongodb_client_initialized() -> bool:
    """Check if MongoDB client is initialized.
    
    Returns:
        bool: True if client is initialized, False otherwise
    """
    return _mongodb_client is not None


async def get_cached_health_status() -> Dict[str, Any]:
    """Get health status immediately from cache.
    
    Returns cached status if fresh, stale status if available, or unknown if no cache.
    This allows sub-5ms response times for health checks.
    
    Returns:
        Dictionary with status, stale flag, and last_checked timestamp
    """
    current_time = time.time()
    
    # Check if we have cached status
    if _health_cache["status"] is not None and _health_cache["last_checked"] is not None:
        age = current_time - _health_cache["last_checked"]
        
        # Return fresh status if within TTL
        if age < _health_cache["ttl"]:
            return {
                "status": _health_cache["status"],
                "stale": False,
                "last_checked": _health_cache["last_checked"],
                "age_seconds": age
            }
        
        # Return stale status if within stale TTL
        if age < _health_cache["stale_ttl"]:
            return {
                "status": _health_cache["status"],
                "stale": True,
                "last_checked": _health_cache["last_checked"],
                "age_seconds": age
            }
    
    # No cache available
    return {
        "status": None,
        "stale": False,
        "last_checked": None,
        "age_seconds": None
    }


async def refresh_health_status_background() -> None:
    """Refresh health status in background.
    
    This function performs the actual MongoDB ping and updates the cache.
    Should be called as a background task.
    """
    try:
        # If client doesn't exist, try to initialize it (lazy initialization)
        if _mongodb_client is None:
            try:
                await get_mongodb_database()
                # get_mongodb_database() already updates health cache on success/failure
                return
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB connection during health check: {e}", exc_info=True)
                _health_cache["status"] = False
                _health_cache["last_checked"] = time.time()
                return
        
        # Test connection with ping
        if IS_LAMBDA:
            # Use safe await for Lambda
            try:
                result = await safe_await_in_lambda(
                    _mongodb_client.admin.command('ping'),
                    "MongoDB health check ping"
                )
                if result is None:
                    # Event loop closed, skip update
                    return
                _health_cache["status"] = True
                _health_cache["last_checked"] = time.time()
            except RuntimeError as e:
                error_msg = str(e)
                if "Event loop is closed" in error_msg or "event loop is closed" in error_msg.lower():
                    return
                raise
        else:
            await _mongodb_client.admin.command('ping')
            _health_cache["status"] = True
            _health_cache["last_checked"] = time.time()
            
    except RuntimeError as e:
        error_msg = str(e)
        if "Event loop is closed" in error_msg or "event loop is closed" in error_msg.lower():
            return
        raise
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}", exc_info=True)
        _health_cache["status"] = False
        _health_cache["last_checked"] = time.time()


async def check_mongodb_health() -> bool:
    """Check MongoDB connection health.
    
    Attempts to initialize connection if not already initialized.
    This provides lazy initialization for cases where lifespan events
    might not have run (e.g., if lifespan is disabled).
    
    Note: For fast responses, use get_cached_health_status() instead.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        # If client doesn't exist, try to initialize it (lazy initialization)
        if _mongodb_client is None:
            try:
                await get_mongodb_database()
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB connection during health check: {e}", exc_info=True)
                return False
        
        # Test connection with ping
        await _mongodb_client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}", exc_info=True)
        return False

