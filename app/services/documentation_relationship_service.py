"""Service for syncing and managing documentation relationships."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.repositories.page_endpoint_relationship_repository import PageEndpointRelationshipRepository
from app.services.documentation_service import DocumentationService
from app.services.endpoint_documentation_service import EndpointDocumentationService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentationRelationshipService:
    """Service for managing documentation relationships."""
    
    def __init__(
        self,
        relationship_repo: Optional[PageEndpointRelationshipRepository] = None,
        doc_service: Optional[DocumentationService] = None,
        endpoint_service: Optional[EndpointDocumentationService] = None
    ):
        """Initialize service with repositories and services."""
        self.relationship_repo = relationship_repo or PageEndpointRelationshipRepository()
        self.doc_service = doc_service or DocumentationService()
        self.endpoint_service = endpoint_service or EndpointDocumentationService()
    
    async def sync_all_relationships(
        self,
        relationships_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync all relationships from analysis data."""
        # Create indexes
        await self.relationship_repo.create_indexes()
        
        page_to_endpoints = relationships_data.get("page_to_endpoints", {})
        endpoint_to_pages = relationships_data.get("endpoint_to_pages", {})
        
        synced_count = 0
        
        # Sync page-to-endpoint relationships
        for page_path, endpoints in page_to_endpoints.items():
            # Generate page_id from page_path
            page_id = page_path.strip("/").replace("/", "_") or "home_page"
            
            # Filter out invalid endpoints
            valid_endpoints = []
            for ep in endpoints:
                try:
                    # Validate endpoint path
                    endpoint_path = ep.get("endpoint_path", "")
                    if not endpoint_path or not endpoint_path.startswith("/api/"):
                        logger.warning(f"Skipping invalid endpoint path: {endpoint_path}")
                        continue
                    
                    # Skip endpoints with malformed paths
                    if endpoint_path.endswith(".md}") or endpoint_path.endswith(".md"):
                        logger.warning(f"Skipping malformed endpoint: {endpoint_path}")
                        continue
                    
                    valid_endpoints.append(ep)
                except Exception as e:
                    logger.warning(f"Skipping invalid endpoint {ep.get('endpoint_path', 'unknown')}: {e}")
                    continue
            
            if not valid_endpoints:
                logger.warning(f"No valid endpoints found for page {page_id}")
                continue
            
            # Update page documentation with endpoints
            try:
                page = await self.doc_service.repository.get_by_page_id(page_id)
                if page:
                    metadata = page.get("metadata", {}).copy()
                    metadata["uses_endpoints"] = valid_endpoints
                    metadata["endpoint_count"] = len(valid_endpoints)
                    api_versions = list(set(ep.get("api_version", "v1") for ep in valid_endpoints))
                    metadata["api_versions"] = api_versions
                    await self.doc_service.update_page(page_id, {"metadata": metadata})
            except Exception as e:
                logger.error(f"Error updating endpoints for page {page_id}: {e}")
                continue
            
            # Create relationship documents
            for endpoint_usage in valid_endpoints:
                try:
                    await self.relationship_repo.create_relationship(
                        page_path=page_path,
                        endpoint_path=endpoint_usage.get("endpoint_path", ""),
                        method=endpoint_usage.get("method", "GET"),
                        api_version=endpoint_usage.get("api_version", "v1"),
                        via_service=endpoint_usage.get("via_service", ""),
                        via_hook=endpoint_usage.get("via_hook"),
                        usage_type=endpoint_usage.get("usage_type", "primary"),
                        usage_context=endpoint_usage.get("usage_context", "data_fetching")
                    )
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Error creating relationship: {e}")
        
        # Sync endpoint-to-page relationships
        for endpoint_key, pages in endpoint_to_pages.items():
            method, endpoint_path = endpoint_key.split(":", 1)
            
            # Find endpoint_id
            endpoint = await self.endpoint_service.get_endpoint_by_path(endpoint_path, method)
            if not endpoint:
                logger.warning(f"Endpoint not found: {endpoint_path} ({method})")
                continue
            
            # Update endpoint documentation with pages
            try:
                endpoint_id = endpoint.get("endpoint_id")
                update_data = {
                    "used_by_pages": pages,
                    "page_count": len(pages)
                }
                await self.endpoint_service.update_endpoint(endpoint_id, update_data)
            except Exception as e:
                logger.error(f"Error updating pages for endpoint {endpoint.get('endpoint_id')}: {e}")
        
        logger.info(f"Synced {synced_count} relationships")
        
        return {
            "synced_relationships": synced_count,
            "pages_updated": len(page_to_endpoints),
            "endpoints_updated": len(endpoint_to_pages)
        }
    
    async def get_endpoint_page_graph(self) -> Dict[str, Any]:
        """Get full relationship graph."""
        relationships = await self.relationship_repo.get_all_relationships()
        
        # Build graph structure
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Collect unique nodes
        pages = set()
        endpoints = set()
        
        for rel in relationships:
            pages.add(rel["page_path"])
            endpoint_key = f"{rel['endpoint_path']} ({rel['method']})"
            endpoints.add(endpoint_key)
        
        # Add page nodes
        for page in pages:
            graph["nodes"].append({
                "id": page,
                "type": "page",
                "label": page
            })
        
        # Add endpoint nodes
        for endpoint in endpoints:
            graph["nodes"].append({
                "id": endpoint,
                "type": "endpoint",
                "label": endpoint
            })
        
        # Add edges
        for rel in relationships:
            endpoint_key = f"{rel['endpoint_path']} ({rel['method']})"
            graph["edges"].append({
                "source": rel["page_path"],
                "target": endpoint_key,
                "via_service": rel.get("via_service", ""),
                "via_hook": rel.get("via_hook"),
                "usage_type": rel.get("usage_type", "primary")
            })
        
        return graph
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get relationship statistics."""
        repo_stats = await self.relationship_repo.get_statistics()
        
        # Get additional stats from services
        all_endpoints = await self.endpoint_service.list_endpoints(limit=1000)
        all_pages = await self.doc_service.list_pages()
        
        return {
            **repo_stats,
            "total_endpoints_documented": all_endpoints.get("total", 0),
            "total_pages_documented": all_pages.get("total", 0),
            "endpoints_with_pages": sum(
                1 for ep in all_endpoints.get("endpoints", [])
                if ep.get("page_count", 0) > 0
            ),
            "pages_with_endpoints": sum(
                1 for page in all_pages.get("pages", [])
                if page.get("metadata", {}).get("endpoint_count", 0) > 0
            )
        }
    
    async def validate_relationships(self) -> Dict[str, Any]:
        """Validate relationships for broken links."""
        issues = []
        
        relationships = await self.relationship_repo.get_all_relationships()
        
        for rel in relationships:
            page_path = rel["page_path"]
            endpoint_path = rel["endpoint_path"]
            method = rel["method"]
            
            # Check if page exists
            page_id = page_path.strip("/").replace("/", "_") or "home_page"
            page = await self.doc_service.get_page_by_id(page_id)
            if not page:
                issues.append({
                    "type": "missing_page",
                    "page_path": page_path,
                    "endpoint_path": endpoint_path,
                    "method": method
                })
            
            # Check if endpoint exists
            endpoint = await self.endpoint_service.get_endpoint_by_path(endpoint_path, method)
            if not endpoint:
                issues.append({
                    "type": "missing_endpoint",
                    "page_path": page_path,
                    "endpoint_path": endpoint_path,
                    "method": method
                })
        
        return {
            "total_relationships": len(relationships),
            "issues": issues,
            "issue_count": len(issues),
            "valid": len(issues) == 0
        }
    
    async def get_pages_for_endpoint(
        self,
        endpoint_path: str,
        method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all pages using a specific endpoint."""
        return await self.relationship_repo.get_pages_for_endpoint(endpoint_path, method)
    
    async def get_endpoints_for_page(
        self,
        page_path: str
    ) -> List[Dict[str, Any]]:
        """Get all endpoints used by a specific page."""
        return await self.relationship_repo.get_endpoints_for_page(page_path)
