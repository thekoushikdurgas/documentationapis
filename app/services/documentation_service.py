"""Service layer for documentation page operations with S3 storage."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.repositories.documentation_repository import DocumentationRepository
from app.services.s3_service import S3Service
from app.core.config import get_settings
from app.core.exceptions import DocumentationNotFoundError, S3Error
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class DocumentationService:
    """Service for documentation pages with S3 storage."""
    
    def __init__(
        self,
        repository: Optional[DocumentationRepository] = None,
        s3_service: Optional[S3Service] = None
    ):
        self.repository = repository or DocumentationRepository()
        self.s3_service = s3_service or S3Service()
        self.docs_prefix = settings.S3_DOCUMENTATION_PREFIX
        self.presigned_expiration = settings.S3_PRESIGNED_URL_EXPIRATION
    
    def _generate_s3_key(self, page_id: str) -> str:
        """Generate S3 key: documentation/{page_id}.md"""
        return f"{self.docs_prefix}{page_id}.md"
    
    async def _upload_to_s3(self, page_id: str, content: str) -> str:
        """Upload markdown to S3. Returns s3_key."""
        s3_key = self._generate_s3_key(page_id)
        content_bytes = content.encode('utf-8')
        
        try:
            await self.s3_service.upload_file(
                file_content=content_bytes,
                s3_key=s3_key,
                content_type="text/markdown; charset=utf-8"
            )
            logger.info(f"Uploaded documentation to S3: {s3_key}")
            return s3_key
        except S3Error as e:
            logger.error(f"S3 upload failed for {page_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload documentation to S3: {str(e)}"
            )
    
    async def _generate_presigned_url(self, s3_key: str) -> tuple[str, datetime]:
        """Generate presigned URL. Returns (url, expiration_datetime)."""
        try:
            url = await self.s3_service.generate_presigned_url(
                s3_key=s3_key,
                expiration=self.presigned_expiration
            )
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.presigned_expiration)
            return url, expires_at
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate content URL: {str(e)}"
            )
    
    async def get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get page metadata from MongoDB + presigned S3 URL."""
        page = await self.repository.get_by_page_id(page_id)
        if not page:
            return None
        
        # Generate presigned URL
        s3_key = page['metadata']['s3_key']
        content_url, expires_at = await self._generate_presigned_url(s3_key)
        
        # Add URL fields to response
        page['content_url'] = content_url
        page['content_url_expires_at'] = expires_at.isoformat()
        
        return page
    
    async def get_page_content(self, page_id: str) -> str:
        """Get markdown content directly from S3 (for proxy endpoint to avoid CORS)."""
        page = await self.repository.get_by_page_id(page_id)
        if not page:
            raise DocumentationNotFoundError(f"Documentation page '{page_id}' not found")
        
        s3_key = page['metadata']['s3_key']
        try:
            content_bytes = await self.s3_service.download_file(s3_key)
            return content_bytes.decode('utf-8')
        except FileNotFoundError:
            logger.error(f"Content not found in S3 for {page_id}: {s3_key}")
            raise DocumentationNotFoundError(f"Content not found for documentation page '{page_id}'")
        except S3Error as e:
            logger.error(f"Failed to download content from S3 for {page_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve content: {str(e)}"
            )
    
    async def list_pages(self) -> Dict[str, Any]:
        """List all pages with presigned URLs."""
        pages = await self.repository.list_all()
        
        # Generate presigned URLs for all pages in parallel
        async def process_page(page: Dict[str, Any]) -> Dict[str, Any]:
            s3_key = page['metadata']['s3_key']
            content_url, expires_at = await self._generate_presigned_url(s3_key)
            page['content_url'] = content_url
            page['content_url_expires_at'] = expires_at.isoformat()
            return page
        
        # Process all pages in parallel
        page_responses = await asyncio.gather(*[process_page(page) for page in pages])
        
        return {
            "pages": list(page_responses),
            "total": len(page_responses)
        }
    
    async def create_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create page: Upload to S3 first, then save metadata to MongoDB (atomic)."""
        content = data.get("content", "")
        page_id = data.get("page_id")
        page_dict = {k: v for k, v in data.items() if k != "content"}
        
        # Step 1: Upload to S3 (fails fast if S3 unavailable)
        s3_key = await self._upload_to_s3(page_id, content)
        
        # Step 2: Add s3_key to metadata
        if "metadata" not in page_dict:
            page_dict["metadata"] = {}
        page_dict['metadata']['s3_key'] = s3_key
        
        try:
            # Step 3: Save to MongoDB
            created = await self.repository.create_page(page_dict)
            
            # Step 4: Generate presigned URL for response
            content_url, expires_at = await self._generate_presigned_url(s3_key)
            created['content_url'] = content_url
            created['content_url_expires_at'] = expires_at.isoformat()
            
            logger.info(f"Created documentation page: {page_id}")
            return created
            
        except Exception as e:
            # Rollback: Delete S3 file if MongoDB fails
            logger.error(f"MongoDB save failed, rolling back S3 upload for {page_id}")
            try:
                await self.s3_service.delete_file(s3_key)
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create documentation page: {str(e)}"
            )
    
    async def update_page(
        self, 
        page_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update page: Update S3 and MongoDB atomically."""
        page_dict = {k: v for k, v in data.items() if k != "content"}
        content = data.get("content")
        
        # Get existing page
        existing = await self.repository.get_by_page_id(page_id)
        if not existing:
            raise DocumentationNotFoundError(f"Documentation page '{page_id}' not found")
        
        s3_key = existing['metadata']['s3_key']
        
        # Step 1: Update S3 if content provided
        if content:
            await self._upload_to_s3(page_id, content)
        
        # Step 2: Update MongoDB metadata if provided
        # Preserve s3_key in metadata if metadata is being updated
        if page_dict and 'metadata' in page_dict:
            # Ensure s3_key is preserved in metadata updates
            page_dict['metadata']['s3_key'] = s3_key
        
        if page_dict:
            updated = await self.repository.update_page(page_id, page_dict)
        else:
            updated = existing
        
        # Step 3: Generate presigned URL
        content_url, expires_at = await self._generate_presigned_url(s3_key)
        updated['content_url'] = content_url
        updated['content_url_expires_at'] = expires_at.isoformat()
        
        logger.info(f"Updated documentation page: {page_id}")
        return updated
    
    async def delete_page(self, page_id: str) -> bool:
        """Delete page: Remove from both S3 and MongoDB."""
        # Get existing page
        existing = await self.repository.get_by_page_id(page_id)
        if not existing:
            return False
        
        s3_key = existing['metadata']['s3_key']
        
        # Step 1: Delete from S3
        try:
            await self.s3_service.delete_file(s3_key)
        except Exception as e:
            logger.error(f"S3 deletion failed for {page_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete S3 file: {str(e)}"
            )
        
        # Step 2: Delete from MongoDB
        try:
            deleted = await self.repository.delete_page(page_id)
            if deleted:
                logger.info(f"Deleted documentation page: {page_id}")
            return deleted
        except Exception as e:
            logger.error(f"MongoDB deletion failed for {page_id}: {e}")
            # S3 already deleted, log the issue but don't fail
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete from database: {str(e)}"
            )
    
    async def get_endpoints_used_by_page(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all endpoints used by a page."""
        page = await self.repository.get_by_page_id(page_id)
        if not page:
            return []
        
        endpoints = page.get("metadata", {}).get("uses_endpoints", [])
        return endpoints
    
    async def get_components_used_by_page(self, page_id: str) -> Dict[str, Any]:
        """Get all components used by a page."""
        page = await self.repository.get_by_page_id(page_id)
        if not page:
            return {}
        
        metadata = page.get("metadata", {})
        return {
            "ui_components": metadata.get("ui_components", []),
            "pattern_components": metadata.get("pattern_components", []),
            "feature_components": metadata.get("feature_components", []),
            "hooks": metadata.get("hooks", []),
            "services": metadata.get("services", []),
            "contexts": metadata.get("contexts", [])
        }
    
    async def sync_from_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync page documentation from analysis data. Creates pages if they don't exist."""
        pages = analysis_data.get("pages", [])
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for page_data in pages:
            try:
                # Generate page_id from page_path
                page_path = page_data.get("page_path", "")
                page_id = page_path.strip("/").replace("/", "_") or "home_page"
                
                # Check if page exists
                existing = await self.repository.get_by_page_id(page_id)
                
                if existing:
                    # Update existing page - update component usage
                    components = {
                        "ui_components": page_data.get("ui_components", []),
                        "pattern_components": page_data.get("pattern_components", []),
                        "feature_components": page_data.get("feature_components", []),
                        "hooks": page_data.get("hooks", []),
                        "services": page_data.get("services", []),
                        "contexts": page_data.get("contexts", [])
                    }
                    
                    # Update metadata with components
                    metadata = existing.get("metadata", {}).copy()
                    metadata.update(components)
                    
                    await self.update_page(page_id, {"metadata": metadata})
                    updated_count += 1
                else:
                    # Create new page with basic metadata
                    page_title = page_data.get("page_title", page_path.strip("/").replace("/", " ").title() or "Home")
                    page_file = page_data.get("page_file", "")
                    
                    # Generate basic markdown content
                    content = f"""# {page_title}

This page is automatically generated from frontend analysis.

## Route
{page_path}

## Components Used

### UI Components
{chr(10).join(f"- {comp}" for comp in page_data.get("ui_components", [])) or "None"}

### Pattern Components
{chr(10).join(f"- {comp}" for comp in page_data.get("pattern_components", [])) or "None"}

### Feature Components
{chr(10).join(f"- {comp}" for comp in page_data.get("feature_components", [])) or "None"}

## Hooks
{chr(10).join(f"- {hook}" for hook in page_data.get("hooks", [])) or "None"}

## Services
{chr(10).join(f"- {service}" for service in page_data.get("services", [])) or "None"}

## Contexts
{chr(10).join(f"- {context}" for context in page_data.get("contexts", [])) or "None"}
"""
                    
                    # Create metadata
                    metadata = {
                        "route": page_path,
                        "file_path": page_file,
                        "s3_key": "",  # Will be set by create_page
                        "authentication": "Not required",
                        "authorization": None,
                        "purpose": f"Frontend page: {page_title}",
                        "last_updated": datetime.utcnow().isoformat(),
                        "ui_components": page_data.get("ui_components", []),
                        "pattern_components": page_data.get("pattern_components", []),
                        "feature_components": page_data.get("feature_components", []),
                        "hooks": page_data.get("hooks", []),
                        "services": page_data.get("services", []),
                        "contexts": page_data.get("contexts", [])
                    }
                    
                    # Create page
                    page_create = {
                        "page_id": page_id,
                        "metadata": metadata,
                        "content": content
                    }
                    
                    await self.create_page(page_create)
                    created_count += 1
                    logger.info(f"Created new page: {page_id}")
                
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing page {page_data.get('page_path')}: {e}")
        
        logger.info(f"Synced {synced_count} pages from analysis (created: {created_count}, updated: {updated_count})")
        return {
            "synced_count": synced_count,
            "created_count": created_count,
            "updated_count": updated_count
        }
