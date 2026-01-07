"""FastAPI dependencies."""

from fastapi import Header, HTTPException, status

from app.clients.mongodb import get_mongodb_database
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing API key header"
        )
    
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid API key"
        )
    
    return x_api_key


async def get_db():
    """Get MongoDB database instance (dependency).
    
    Yields:
        MongoDB database instance
    """
    db = await get_mongodb_database()
    yield db

