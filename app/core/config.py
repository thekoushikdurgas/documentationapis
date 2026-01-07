"""Application configuration objects and helpers."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment and defaults."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Project
    PROJECT_NAME: str = "Documentation API Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Centralized documentation microservice for Contact360 application"
    ENVIRONMENT: str = Field("development", alias="APP_ENV")
    DEBUG: bool = Field(False, alias="DEBUG")
    
    # API
    PORT: int = Field(8080, alias="PORT")
    API_KEY: str = Field(..., alias="API_KEY", description="API key for service-to-service authentication (required)")
    
    # MongoDB Configuration
    MONGODB_URI: Optional[str] = Field(None, alias="MONGODB_URI", description="MongoDB connection URI")
    MONGODB_DB_NAME: str = Field("documentation", alias="MONGODB_DB_NAME", description="Database name")
    MONGODB_USER: Optional[str] = Field(None, alias="MONGODB_USER", description="MongoDB username (if auth enabled)")
    MONGODB_PASSWORD: Optional[str] = Field(None, alias="MONGODB_PASSWORD", description="MongoDB password (if auth enabled)")
    MONGODB_HOST: Optional[str] = Field(None, alias="MONGODB_HOST", description="MongoDB host (if not using URI)")
    MONGODB_PORT: Optional[str] = Field(None, alias="MONGODB_PORT", description="MongoDB port (if not using URI)")
    MONGODB_AUTH: bool = Field(False, alias="MONGODB_AUTH", description="Enable MongoDB authentication")
    MONGODB_DEBUG: bool = Field(False, alias="MONGODB_DEBUG", description="Enable MongoDB debug logging")
    
    # MongoDB Connection Pooling (Optimization)
    MONGODB_MAX_POOL_SIZE: int = Field(100, alias="MONGODB_MAX_POOL_SIZE", description="Maximum connection pool size")
    MONGODB_MIN_POOL_SIZE: int = Field(10, alias="MONGODB_MIN_POOL_SIZE", description="Minimum connection pool size")
    MONGODB_MAX_IDLE_TIME_MS: int = Field(30000, alias="MONGODB_MAX_IDLE_TIME_MS", description="Max idle time for connections (30s)")
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    
    # Query Caching (Optimization)
    ENABLE_QUERY_CACHING: bool = Field(True, alias="ENABLE_QUERY_CACHING", description="Enable query result caching")
    QUERY_CACHE_TTL: int = Field(300, alias="QUERY_CACHE_TTL", description="Query cache TTL in seconds (5 minutes)")
    QUERY_CACHE_MAX_SIZE: int = Field(1000, alias="QUERY_CACHE_MAX_SIZE", description="Maximum cache entries")
    CACHE_STALE_TTL_MULTIPLIER: float = Field(2.0, alias="CACHE_STALE_TTL_MULTIPLIER", description="Multiplier for stale TTL (default: 2x)")
    
    # Query Monitoring (Optimization)
    ENABLE_QUERY_MONITORING: bool = Field(True, alias="ENABLE_QUERY_MONITORING", description="Enable query performance monitoring")
    SLOW_QUERY_THRESHOLD: float = Field(1.0, alias="SLOW_QUERY_THRESHOLD", description="Slow query threshold in seconds")
    
    # Batch Operations (Optimization)
    BATCH_SIZE_LIMIT: int = Field(1000, alias="BATCH_SIZE_LIMIT", description="Maximum batch size for bulk operations")
    
    # S3 Configuration
    S3_BUCKET_NAME: str = Field(..., alias="S3_BUCKET_NAME", description="S3 bucket name for documentation storage")
    S3_DOCUMENTATION_PREFIX: str = Field("documentation/", alias="S3_DOCUMENTATION_PREFIX", description="S3 prefix for documentation files")
    S3_PRESIGNED_URL_EXPIRATION: int = Field(3600, alias="S3_PRESIGNED_URL_EXPIRATION", description="Presigned URL expiration in seconds (default: 1 hour)")
    AWS_REGION: str = Field("us-east-1", alias="AWS_REGION", description="AWS region (automatically set by Lambda, default for local development)")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID", description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY", description="AWS secret access key")
    
    # Cache Metrics
    CACHE_METRICS_ENABLED: bool = Field(True, alias="CACHE_METRICS_ENABLED", description="Enable cache metrics collection")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

