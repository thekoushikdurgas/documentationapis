"""Documentation relationships API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.dependencies import verify_api_key
from app.services.documentation_relationship_service import DocumentationRelationshipService
from app.schemas.requests import SyncRequest
from app.schemas.responses import (
    RelationshipGraphResponse,
    RelationshipStatisticsResponse,
    ValidationResponse,
    SuccessResponse
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/docs/relationships", tags=["Documentation Relationships"])
service = DocumentationRelationshipService()


# ============= ENDPOINTS (API key required) =============

@router.get("/graph", response_model=RelationshipGraphResponse)
async def get_relationship_graph(
    api_key: str = Depends(verify_api_key),
) -> RelationshipGraphResponse:
    """Get full relationship graph (nodes and edges)."""
    try:
        graph = await service.get_endpoint_page_graph()
        # Service returns dict, convert to response model
        return RelationshipGraphResponse(**graph)
    except Exception as e:
        logger.error(f"Failed to get relationship graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get relationship graph: {str(e)}"
        )


@router.get("/endpoint/{endpoint_path:path}")
async def get_pages_for_endpoint(
    endpoint_path: str,
    method: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get all pages using a specific endpoint."""
    try:
        pages = await service.get_pages_for_endpoint(endpoint_path, method)
        return {"pages": pages}
    except Exception as e:
        logger.error(f"Failed to get pages for endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pages for endpoint: {str(e)}"
        )


@router.get("/page/{page_path:path}")
async def get_endpoints_for_page(
    page_path: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get all endpoints used by a specific page."""
    try:
        endpoints = await service.get_endpoints_for_page(page_path)
        return {"endpoints": endpoints}
    except Exception as e:
        logger.error(f"Failed to get endpoints for page: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get endpoints for page: {str(e)}"
        )


@router.get("/statistics", response_model=RelationshipStatisticsResponse)
async def get_statistics(
    api_key: str = Depends(verify_api_key),
) -> RelationshipStatisticsResponse:
    """Get relationship statistics."""
    try:
        stats = await service.get_statistics()
        # Service returns dict, convert to response model
        return RelationshipStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/sync", response_model=SuccessResponse)
async def sync_relationships(
    data: SyncRequest,
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """
    Sync all relationships from analysis data (Admin only, API key required).
    Creates relationships between pages and endpoints.
    """
    try:
        relationships_data = data.relationships or {}
        result = await service.sync_all_relationships(relationships_data)
        return SuccessResponse(
            success=True,
            message=f"Synced {result.get('synced_relationships', 0)} relationships",
            data=result
        )
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync relationships: {str(e)}"
        )


@router.get("/validate", response_model=ValidationResponse)
async def validate_relationships(
    api_key: str = Depends(verify_api_key),
) -> ValidationResponse:
    """Validate relationships for broken links (Admin only, API key required)."""
    try:
        validation = await service.validate_relationships()
        # Service returns dict, convert to response model
        return ValidationResponse(**validation)
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate relationships: {str(e)}"
        )
