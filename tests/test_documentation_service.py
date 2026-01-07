"""Unit tests for documentation service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.documentation_service import DocumentationService
from app.repositories.documentation_repository import DocumentationRepository
from app.services.s3_service import S3Service


@pytest.fixture
def mock_repository():
    """Mock documentation repository."""
    return AsyncMock(spec=DocumentationRepository)


@pytest.fixture
def mock_s3_service():
    """Mock S3 service."""
    return AsyncMock(spec=S3Service)


@pytest.fixture
def service(mock_repository, mock_s3_service):
    """Create documentation service with mocked dependencies."""
    return DocumentationService(
        repository=mock_repository,
        s3_service=mock_s3_service
    )


@pytest.mark.asyncio
async def test_get_page_by_id_success(service, mock_repository, mock_s3_service):
    """Test successful page retrieval."""
    page_id = "test_page"
    mock_page = {
        "_id": "123",
        "page_id": page_id,
        "metadata": {
            "route": "/test",
            "s3_key": "documentation/test_page.md"
        },
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    mock_repository.get_by_page_id.return_value = mock_page
    mock_s3_service.generate_presigned_url.return_value = (
        "https://s3.amazonaws.com/presigned-url",
        "2024-01-01T01:00:00Z"
    )
    
    result = await service.get_page_by_id(page_id)
    
    assert result is not None
    assert result["page_id"] == page_id
    assert "content_url" in result
    mock_repository.get_by_page_id.assert_called_once_with(page_id)


@pytest.mark.asyncio
async def test_get_page_by_id_not_found(service, mock_repository):
    """Test page not found."""
    page_id = "nonexistent_page"
    mock_repository.get_by_page_id.return_value = None
    
    result = await service.get_page_by_id(page_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_create_page_success(service, mock_repository, mock_s3_service):
    """Test successful page creation."""
    page_data = {
        "page_id": "new_page",
        "metadata": {
            "route": "/new",
            "purpose": "Test page"
        },
        "content": "# Test Content"
    }
    
    mock_s3_service.upload_file.return_value = "documentation/new_page.md"
    mock_repository.create_page.return_value = {
        "_id": "123",
        **page_data,
        "metadata": {
            **page_data["metadata"],
            "s3_key": "documentation/new_page.md"
        },
        "created_at": "2024-01-01T00:00:00Z"
    }
    mock_s3_service.generate_presigned_url.return_value = (
        "https://s3.amazonaws.com/presigned-url",
        "2024-01-01T01:00:00Z"
    )
    
    result = await service.create_page(page_data)
    
    assert result is not None
    assert result["page_id"] == "new_page"
    mock_s3_service.upload_file.assert_called_once()
    mock_repository.create_page.assert_called_once()
