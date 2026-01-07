"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import documentation, endpoint_documentation, documentation_relationships

api_router = APIRouter()

# Include documentation endpoints
api_router.include_router(documentation.router, tags=["Documentation"])
api_router.include_router(endpoint_documentation.router, tags=["Endpoint Documentation"])
api_router.include_router(documentation_relationships.router, tags=["Documentation Relationships"])
