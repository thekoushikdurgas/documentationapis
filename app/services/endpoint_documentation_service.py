"""Service layer for endpoint documentation operations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.repositories.endpoint_documentation_repository import EndpointDocumentationRepository
from app.core.exceptions import EndpointDocumentationNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EndpointDocumentationService:
    """Service for endpoint documentation operations."""
    
    def __init__(self, repository: Optional[EndpointDocumentationRepository] = None):
        """Initialize service with repository."""
        self.repository = repository or EndpointDocumentationRepository()
    
    async def get_endpoint_by_id(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get endpoint documentation by ID."""
        endpoint = await self.repository.get_by_endpoint_id(endpoint_id)
        if not endpoint:
            return None
        return endpoint
    
    async def get_endpoint_by_path(
        self,
        endpoint_path: str,
        method: str
    ) -> Optional[Dict[str, Any]]:
        """Get endpoint documentation by path and method."""
        endpoint = await self.repository.get_by_path_and_method(endpoint_path, method)
        if not endpoint:
            return None
        return endpoint
    
    async def list_endpoints(
        self,
        api_version: Optional[str] = None,
        method: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all endpoints with optional filters."""
        filters = {}
        if api_version:
            filters["api_version"] = api_version
        if method:
            filters["method"] = method
        
        endpoints = await self.repository.list_all(filters=filters, limit=limit, offset=offset)
        total = await self.repository.count(filters=filters)
        
        return {
            "endpoints": endpoints,
            "total": total
        }
    
    async def get_pages_using_endpoint(
        self,
        endpoint_path: str,
        method: str
    ) -> List[Dict[str, Any]]:
        """Get all pages using a specific endpoint."""
        endpoint = await self.repository.get_by_path_and_method(endpoint_path, method)
        if not endpoint:
            return []
        
        pages = endpoint.get("used_by_pages", [])
        return pages
    
    async def create_endpoint(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create endpoint documentation."""
        endpoint_dict = data.copy()
        endpoint_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        endpoint_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        endpoint_dict["used_by_pages"] = []
        endpoint_dict["page_count"] = 0
        
        created = await self.repository.create_endpoint(endpoint_dict)
        
        logger.info(f"Created endpoint documentation: {data.get('endpoint_id')}")
        return created
    
    async def update_endpoint(
        self,
        endpoint_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update endpoint documentation."""
        existing = await self.repository.get_by_endpoint_id(endpoint_id)
        if not existing:
            raise EndpointDocumentationNotFoundError(f"Endpoint documentation '{endpoint_id}' not found")
        
        update_dict = {k: v for k, v in data.items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        updated = await self.repository.update_endpoint(endpoint_id, update_dict)
        
        logger.info(f"Updated endpoint documentation: {endpoint_id}")
        return updated
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete endpoint documentation."""
        deleted = await self.repository.delete_endpoint(endpoint_id)
        if deleted:
            logger.info(f"Deleted endpoint documentation: {endpoint_id}")
        return deleted
    
    async def sync_from_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync endpoint documentation from analysis data."""
        endpoints = analysis_data.get("endpoints", [])
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for endpoint_data in endpoints:
            try:
                endpoint_id = endpoint_data.get("endpoint_id")
                if not endpoint_id:
                    continue
                
                # Check if endpoint exists
                existing = await self.repository.get_by_endpoint_id(endpoint_id)
                
                if existing:
                    # Update existing
                    update_data = {
                        "router_file": endpoint_data.get("router_file"),
                        "service_methods": endpoint_data.get("service_methods", []),
                        "repository_methods": endpoint_data.get("repository_methods", []),
                        "authentication": endpoint_data.get("authentication", "Not specified"),
                        "authorization": endpoint_data.get("authorization"),
                        "rate_limit": endpoint_data.get("rate_limit"),
                        "description": endpoint_data.get("description", ""),
                        "sql_file": endpoint_data.get("sql_file")
                    }
                    await self.update_endpoint(endpoint_id, update_data)
                    updated_count += 1
                else:
                    # Create new
                    create_data = {
                        "endpoint_id": endpoint_id,
                        "endpoint_path": endpoint_data.get("endpoint_path", ""),
                        "method": endpoint_data.get("method", "GET"),
                        "api_version": endpoint_data.get("api_version", "v1"),
                        "router_file": endpoint_data.get("router_file", ""),
                        "service_methods": endpoint_data.get("service_methods", []),
                        "repository_methods": endpoint_data.get("repository_methods", []),
                        "authentication": endpoint_data.get("authentication", "Not specified"),
                        "authorization": endpoint_data.get("authorization"),
                        "rate_limit": endpoint_data.get("rate_limit"),
                        "description": endpoint_data.get("description", ""),
                        "sql_file": endpoint_data.get("sql_file")
                    }
                    await self.create_endpoint(create_data)
                    created_count += 1
                
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing endpoint {endpoint_data.get('endpoint_id')}: {e}")
        
        logger.info(f"Synced {synced_count} endpoints from analysis (created: {created_count}, updated: {updated_count})")
        return {
            "synced_count": synced_count,
            "created_count": created_count,
            "updated_count": updated_count
        }
