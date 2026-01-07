"""Request schemas for documentation API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentationPageCreateRequest(BaseModel):
    """Create documentation page request."""
    
    page_id: str = Field(..., description="Unique page ID")
    metadata: Dict[str, Any] = Field(..., description="Page metadata")
    content: str = Field(..., description="Markdown content")


class DocumentationPageUpdateRequest(BaseModel):
    """Update documentation page request."""
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    content: Optional[str] = Field(None, description="Updated markdown content")


class EndpointDocumentationCreateRequest(BaseModel):
    """Create endpoint documentation request."""
    
    endpoint_id: str = Field(..., description="Unique endpoint ID")
    endpoint_path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    api_version: str = Field(..., description="API version")
    router_file: str = Field(..., description="Router file path")
    service_methods: List[str] = Field(default_factory=list)
    repository_methods: List[str] = Field(default_factory=list)
    authentication: str = Field(default="Not specified")
    authorization: Optional[str] = None
    rate_limit: Optional[str] = None
    description: str = Field(..., description="Endpoint description")
    sql_file: Optional[str] = None


class EndpointDocumentationUpdateRequest(BaseModel):
    """Update endpoint documentation request."""
    
    router_file: Optional[str] = None
    service_methods: Optional[List[str]] = None
    repository_methods: Optional[List[str]] = None
    authentication: Optional[str] = None
    authorization: Optional[str] = None
    rate_limit: Optional[str] = None
    description: Optional[str] = None
    sql_file: Optional[str] = None
    used_by_pages: Optional[List[Dict[str, Any]]] = None
    page_count: Optional[int] = None


class SyncRequest(BaseModel):
    """Sync request for analysis data."""
    
    pages: Optional[List[Dict[str, Any]]] = None
    endpoints: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[Dict[str, Any]] = None
