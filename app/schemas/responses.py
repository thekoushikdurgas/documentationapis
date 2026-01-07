"""Response schemas for documentation API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentationPageResponse(BaseModel):
    """Documentation page response."""
    
    id: Optional[str] = Field(None, alias="_id")
    page_id: str
    metadata: Dict[str, Any]
    created_at: str
    content_url: str
    content_url_expires_at: str


class DocumentationPageListResponse(BaseModel):
    """List of documentation pages response."""
    
    pages: List[DocumentationPageResponse]
    total: int


class EndpointDocumentationResponse(BaseModel):
    """Endpoint documentation response."""
    
    id: Optional[str] = Field(None, alias="_id")
    endpoint_id: str
    endpoint_path: str
    method: str
    api_version: str
    router_file: str
    service_methods: List[str]
    repository_methods: List[str]
    authentication: str
    authorization: Optional[str]
    rate_limit: Optional[str]
    description: str
    sql_file: Optional[str]
    used_by_pages: List[Dict[str, Any]] = Field(default_factory=list)
    page_count: int = Field(default=0)
    created_at: str
    updated_at: str


class EndpointDocumentationListResponse(BaseModel):
    """List of endpoint documentation response."""
    
    endpoints: List[EndpointDocumentationResponse]
    total: int


class RelationshipGraphResponse(BaseModel):
    """Relationship graph response."""
    
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class RelationshipStatisticsResponse(BaseModel):
    """Relationship statistics response."""
    
    total_relationships: int
    unique_pages: int
    unique_endpoints: int
    by_api_version: Dict[str, int]
    total_endpoints_documented: int
    total_pages_documented: int
    endpoints_with_pages: int
    pages_with_endpoints: int


class ValidationResponse(BaseModel):
    """Validation response."""
    
    total_relationships: int
    issues: List[Dict[str, Any]]
    issue_count: int
    valid: bool


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
