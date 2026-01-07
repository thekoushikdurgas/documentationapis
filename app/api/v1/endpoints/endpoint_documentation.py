"""Endpoint documentation API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import verify_api_key
from app.core.exceptions import EndpointDocumentationNotFoundError
from app.services.endpoint_documentation_service import EndpointDocumentationService
from app.schemas.requests import EndpointDocumentationCreateRequest, EndpointDocumentationUpdateRequest, SyncRequest
from app.schemas.responses import (
    EndpointDocumentationResponse,
    EndpointDocumentationListResponse,
    SuccessResponse
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/endpoint-docs", tags=["Endpoint Documentation"])
service = EndpointDocumentationService()


# ============= ENDPOINTS (API key required) =============

@router.get("/", response_model=EndpointDocumentationListResponse)
async def list_endpoints(
    api_version: Optional[str] = Query(None, description="Filter by API version"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    api_key: str = Depends(verify_api_key),
) -> EndpointDocumentationListResponse:
    """List all endpoint documentation with optional filters."""
    result = await service.list_endpoints(
        api_version=api_version,
        method=method,
        limit=limit,
        offset=offset
    )
    # Service returns dict, convert to response model
    return EndpointDocumentationListResponse(**result)


@router.get("/{endpoint_id}", response_model=EndpointDocumentationResponse)
async def get_endpoint(
    endpoint_id: str,
    api_key: str = Depends(verify_api_key),
) -> EndpointDocumentationResponse:
    """Get endpoint documentation by ID."""
    endpoint = await service.get_endpoint_by_id(endpoint_id)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint documentation '{endpoint_id}' not found"
        )
    # Service returns dict, convert to response model
    return EndpointDocumentationResponse(**endpoint)


@router.get("/{endpoint_id}/pages")
async def get_endpoint_pages(
    endpoint_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get all pages using a specific endpoint."""
    endpoint = await service.get_endpoint_by_id(endpoint_id)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint documentation '{endpoint_id}' not found"
        )
    
    pages = endpoint.get("used_by_pages", [])
    return {"pages": pages}


@router.post("/", response_model=EndpointDocumentationResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    data: EndpointDocumentationCreateRequest,
    api_key: str = Depends(verify_api_key),
) -> EndpointDocumentationResponse:
    """Create endpoint documentation (Admin only, API key required)."""
    try:
        endpoint_dict = data.model_dump()
        result = await service.create_endpoint(endpoint_dict)
        # Service returns dict, convert to response model
        return EndpointDocumentationResponse(**result)
    except Exception as e:
        logger.error(f"Create failed for {data.endpoint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create endpoint documentation: {str(e)}"
        )


@router.put("/{endpoint_id}", response_model=EndpointDocumentationResponse)
async def update_endpoint(
    endpoint_id: str,
    data: EndpointDocumentationUpdateRequest,
    api_key: str = Depends(verify_api_key),
) -> EndpointDocumentationResponse:
    """Update endpoint documentation (Admin only, API key required)."""
    try:
        endpoint_dict = data.model_dump(exclude_none=True)
        result = await service.update_endpoint(endpoint_id, endpoint_dict)
        # Service returns dict, convert to response model
        return EndpointDocumentationResponse(**result)
    except EndpointDocumentationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update failed for {endpoint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update endpoint documentation: {str(e)}"
        )


@router.delete("/{endpoint_id}", response_model=SuccessResponse)
async def delete_endpoint(
    endpoint_id: str,
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """Delete endpoint documentation (Admin only, API key required)."""
    try:
        deleted = await service.delete_endpoint(endpoint_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Endpoint documentation '{endpoint_id}' not found"
            )
        return SuccessResponse(
            success=True,
            message=f"Endpoint documentation '{endpoint_id}' deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed for {endpoint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete endpoint documentation: {str(e)}"
        )


@router.post("/sync", response_model=SuccessResponse)
async def sync_endpoints(
    data: SyncRequest,
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """
    Sync endpoint documentation from analysis data (Admin only, API key required).
    Creates endpoints if they don't exist, updates if they do.
    """
    try:
        analysis_data = {
            "endpoints": data.endpoints or []
        }
        result = await service.sync_from_analysis(analysis_data)
        return SuccessResponse(
            success=True,
            message=f"Synced {result.get('synced_count', 0)} endpoints",
            data=result
        )
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync endpoints: {str(e)}"
        )
