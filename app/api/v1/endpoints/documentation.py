"""Documentation page API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.dependencies import verify_api_key
from app.core.exceptions import DocumentationNotFoundError
from app.services.documentation_service import DocumentationService
from app.schemas.requests import DocumentationPageCreateRequest, DocumentationPageUpdateRequest, SyncRequest
from app.schemas.responses import (
    DocumentationPageResponse,
    DocumentationPageListResponse,
    SuccessResponse
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/docs", tags=["Documentation"])
service = DocumentationService()


# ============= PUBLIC ENDPOINTS (No auth required) =============

@router.get("/", response_model=DocumentationPageListResponse)
async def list_documentation_pages() -> DocumentationPageListResponse:
    """
    List all documentation pages (public endpoint).
    Returns metadata + presigned S3 URLs for content.
    """
    result = await service.list_pages()
    # Service returns dict, convert to response model
    return DocumentationPageListResponse(**result)


@router.get("/{page_id}", response_model=DocumentationPageResponse)
async def get_documentation_page(page_id: str) -> DocumentationPageResponse:
    """
    Get documentation page (public endpoint).
    Returns metadata + presigned S3 URL for markdown content.
    """
    page = await service.get_page_by_id(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documentation page '{page_id}' not found"
        )
    return DocumentationPageResponse(**page)


@router.get("/{page_id}/content")
async def get_documentation_page_content(page_id: str) -> Response:
    """
    Get documentation page markdown content (public endpoint).
    Proxy endpoint that fetches content from S3 to avoid CORS issues.
    Returns plain text markdown content.
    """
    try:
        content = await service.get_page_content(page_id)
        return Response(content=content, media_type="text/markdown; charset=utf-8")
    except DocumentationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{page_id}/endpoints")
async def get_page_endpoints(page_id: str) -> dict:
    """Get all endpoints used by a page (public endpoint)."""
    endpoints = await service.get_endpoints_used_by_page(page_id)
    return {"endpoints": endpoints}


@router.get("/{page_id}/components")
async def get_page_components(page_id: str) -> dict:
    """Get all components used by a page (public endpoint)."""
    components = await service.get_components_used_by_page(page_id)
    return components


# ============= ADMIN ENDPOINTS (API key required) =============

@router.post("/", response_model=DocumentationPageResponse, status_code=status.HTTP_201_CREATED)
async def create_documentation_page(
    data: DocumentationPageCreateRequest,
    api_key: str = Depends(verify_api_key),
) -> DocumentationPageResponse:
    """
    Create new documentation page (Admin only, API key required).
    Uploads markdown to S3 and saves metadata to MongoDB.
    """
    try:
        page_dict = data.model_dump()
        result = await service.create_page(page_dict)
        return DocumentationPageResponse(**result)
    except Exception as e:
        logger.error(f"Create failed for {data.page_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create documentation page: {str(e)}"
        )


@router.put("/{page_id}", response_model=DocumentationPageResponse)
async def update_documentation_page(
    page_id: str,
    data: DocumentationPageUpdateRequest,
    api_key: str = Depends(verify_api_key),
) -> DocumentationPageResponse:
    """
    Update documentation page (Admin only, API key required).
    Updates S3 content and/or MongoDB metadata.
    """
    try:
        page_dict = data.model_dump(exclude_none=True)
        result = await service.update_page(page_id, page_dict)
        # Service returns dict, convert to response model
        return DocumentationPageResponse(**result)
    except DocumentationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update failed for {page_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update documentation page: {str(e)}"
        )


@router.delete("/{page_id}", response_model=SuccessResponse)
async def delete_documentation_page(
    page_id: str,
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """
    Delete documentation page (Admin only, API key required).
    Removes from both S3 and MongoDB.
    """
    try:
        deleted = await service.delete_page(page_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documentation page '{page_id}' not found"
            )
        return SuccessResponse(
            success=True,
            message=f"Documentation page '{page_id}' deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed for {page_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documentation page: {str(e)}"
        )


@router.post("/sync", response_model=SuccessResponse)
async def sync_pages(
    data: SyncRequest,
    api_key: str = Depends(verify_api_key),
) -> SuccessResponse:
    """
    Sync documentation pages from analysis data (Admin only, API key required).
    Creates pages if they don't exist, updates if they do.
    """
    try:
        analysis_data = {
            "pages": data.pages or []
        }
        result = await service.sync_from_analysis(analysis_data)
        return SuccessResponse(
            success=True,
            message=f"Synced {result.get('synced_count', 0)} pages",
            data=result
        )
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync pages: {str(e)}"
        )
