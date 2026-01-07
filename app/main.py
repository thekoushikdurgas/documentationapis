"""FastAPI application main entry point."""

import utils.transport
import utils.session
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.clients.mongodb import (
    check_mongodb_health,
    close_mongodb_connection,
    get_cached_health_status,
    get_mongodb_database,
    is_mongodb_client_initialized,
    refresh_health_status_background,
)
from app.utils.background_tasks import add_background_task_safe
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    DatabaseError,
    DocumentationAPIException,
    DocumentationNotFoundError,
    EndpointDocumentationNotFoundError,
    InvalidDocumentationIDError,
    S3Error,
    ValidationError,
)
from app.middleware.compression import CompressionMiddleware
from app.middleware.monitoring import MonitoringMiddleware
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    try:
        # Initialize MongoDB connection
        await get_mongodb_database()
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    await close_mongodb_connection()


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    redirect_slashes=False,  # Disable automatic redirects for trailing slashes
)

# CORS middleware (allow all origins for service-to-service communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware (GZip for responses >1KB)
app.add_middleware(CompressionMiddleware, minimum_size=1024)

# Monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Include API router
app.include_router(api_router, prefix="")


# Exception handlers
@app.exception_handler(DocumentationAPIException)
async def documentation_api_exception_handler(request, exc: DocumentationAPIException):
    """Handle custom exceptions."""
    status_code = 500
    if isinstance(exc, (InvalidDocumentationIDError, DocumentationNotFoundError, EndpointDocumentationNotFoundError)):
        status_code = 404
    elif isinstance(exc, ValidationError):
        status_code = 400
    elif isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, (DatabaseError, S3Error)):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "success": False,
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check(background_tasks: BackgroundTasks):
    """Health check endpoint with cached MongoDB status.
    
    Returns cached health status immediately (<5ms) and refreshes in background if stale.
    """
    
    # Get cached status immediately (<5ms)
    health_data = await get_cached_health_status()
    
    # Get diagnostic information for troubleshooting
    diagnostics = {
        "client_initialized": is_mongodb_client_initialized(),
        "mongodb_uri_configured": bool(settings.MONGODB_URI),
        "mongodb_db_name": settings.MONGODB_DB_NAME,
        "s3_bucket_configured": bool(settings.S3_BUCKET_NAME),
    }
    
    # Determine status from cached data
    db_healthy = health_data.get("status", False)
    is_stale = health_data.get("stale", False)
    
    # Trigger background refresh if cache is stale or missing
    if is_stale or health_data.get("status") is None:
        add_background_task_safe(
            background_tasks,
            refresh_health_status_background
        )
    
    # Build response
    response = {
        "status": "ok" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "diagnostics": diagnostics,
        "cache": {
            "cached": health_data.get("status") is not None,
            "stale": is_stale,
            "age_seconds": health_data.get("age_seconds"),
            "last_checked": health_data.get("last_checked"),
        }
    }
    
    return response  # <5ms response time


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
    }


# Lambda handler for AWS Lambda deployment
def handler(event, context):
    """AWS Lambda handler function.
    
    This handler adapts the FastAPI application for AWS Lambda.
    It can be used with:
    - Lambda Function URL (direct HTTP)
    - API Gateway (REST API)
    - Application Load Balancer
    
    Args:
        event: Lambda event (dict or API Gateway event)
        context: Lambda context object
        
    Returns:
        Response dict with statusCode, headers, and body
    """
    from mangum import Mangum
    
    # Create Mangum adapter for FastAPI with lifespan enabled
    # Using "auto" enables lifespan events (startup/shutdown) for MongoDB connection management
    asgi_handler = Mangum(app, lifespan="auto")
    
    # Handle the event
    return asgi_handler(event, context)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
