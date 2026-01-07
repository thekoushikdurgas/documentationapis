"""Repository for page-endpoint relationships."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.clients.mongodb import get_mongodb_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PageEndpointRelationshipRepository:
    """Repository for managing page-endpoint relationships."""
    
    def __init__(self, database: Optional[AsyncIOMotorDatabase] = None):
        """Initialize repository with MongoDB database."""
        self.database = database
        self.collection_name = "page_endpoint_relationships"
    
    async def _get_collection(self):
        """Get MongoDB collection."""
        if self.database is None:
            self.database = await get_mongodb_database()
        return self.database[self.collection_name]
    
    async def create_indexes(self):
        """Create indexes for efficient queries."""
        collection = await self._get_collection()
        
        # Compound unique index
        await collection.create_index(
            [("page_path", 1), ("endpoint_path", 1), ("method", 1)],
            unique=True,
            name="page_endpoint_method_unique"
        )
        
        # Index for page lookups
        await collection.create_index(
            [("page_path", 1)],
            name="page_path_idx"
        )
        
        # Index for endpoint lookups
        await collection.create_index(
            [("endpoint_path", 1)],
            name="endpoint_path_idx"
        )
        
        # Index for API version filtering
        await collection.create_index(
            [("api_version", 1)],
            name="api_version_idx"
        )
        
    
    async def create_relationship(
        self,
        page_path: str,
        endpoint_path: str,
        method: str,
        api_version: str,
        via_service: str,
        via_hook: Optional[str] = None,
        usage_type: str = "primary",
        usage_context: str = "data_fetching"
    ) -> Dict:
        """Create or update a page-endpoint relationship."""
        collection = await self._get_collection()
        
        # Build relationship data without timestamps
        # created_at should only be set on insert, updated_at should always be updated
        relationship = {
            "page_path": page_path,
            "endpoint_path": endpoint_path,
            "method": method,
            "api_version": api_version,
            "via_service": via_service,
            "via_hook": via_hook,
            "usage_type": usage_type,
            "usage_context": usage_context,
        }
        
        now = datetime.now(timezone.utc)
        
        # Use upsert to create or update
        # $setOnInsert only sets created_at on insert, not on update
        # $set always updates updated_at and other fields
        result = await collection.update_one(
            {
                "page_path": page_path,
                "endpoint_path": endpoint_path,
                "method": method
            },
            {
                "$set": {
                    **relationship,
                    "updated_at": now
                },
                "$setOnInsert": {"created_at": now}
            },
            upsert=True
        )
        
        if result.upserted_id:
            relationship["_id"] = result.upserted_id
        else:
            # Get existing document
            existing = await collection.find_one({
                "page_path": page_path,
                "endpoint_path": endpoint_path,
                "method": method
            })
            if existing:
                relationship["_id"] = existing["_id"]
        
        return relationship
    
    async def get_pages_for_endpoint(
        self,
        endpoint_path: str,
        method: Optional[str] = None
    ) -> List[Dict]:
        """Get all pages using a specific endpoint."""
        collection = await self._get_collection()
        
        query = {"endpoint_path": endpoint_path}
        if method:
            query["method"] = method
        
        cursor = collection.find(query)
        pages = await cursor.to_list(length=None)
        
        return pages
    
    async def get_endpoints_for_page(
        self,
        page_path: str
    ) -> List[Dict]:
        """Get all endpoints used by a specific page."""
        collection = await self._get_collection()
        
        cursor = collection.find({"page_path": page_path})
        endpoints = await cursor.to_list(length=None)
        
        return endpoints
    
    async def get_all_relationships(self) -> List[Dict]:
        """Get all relationships."""
        collection = await self._get_collection()
        
        cursor = collection.find({})
        relationships = await cursor.to_list(length=None)
        
        return relationships
    
    async def delete_relationship(
        self,
        page_path: str,
        endpoint_path: str,
        method: str
    ) -> bool:
        """Delete a specific relationship."""
        collection = await self._get_collection()
        
        result = await collection.delete_one({
            "page_path": page_path,
            "endpoint_path": endpoint_path,
            "method": method
        })
        
        return result.deleted_count > 0
    
    async def delete_all_for_page(self, page_path: str) -> int:
        """Delete all relationships for a page."""
        collection = await self._get_collection()
        
        result = await collection.delete_many({"page_path": page_path})
        
        return result.deleted_count
    
    async def delete_all_for_endpoint(
        self,
        endpoint_path: str,
        method: Optional[str] = None
    ) -> int:
        """Delete all relationships for an endpoint."""
        collection = await self._get_collection()
        
        query = {"endpoint_path": endpoint_path}
        if method:
            query["method"] = method
        
        result = await collection.delete_many(query)
        
        return result.deleted_count
    
    async def get_statistics(self) -> Dict:
        """Get relationship statistics."""
        collection = await self._get_collection()
        
        total_relationships = await collection.count_documents({})
        
        # Count unique pages
        unique_pages = await collection.distinct("page_path")
        
        # Count unique endpoints
        unique_endpoints = await collection.distinct("endpoint_path")
        
        # Count by API version
        pipeline = [
            {"$group": {"_id": "$api_version", "count": {"$sum": 1}}}
        ]
        version_counts = {}
        async for doc in collection.aggregate(pipeline):
            version_counts[doc["_id"]] = doc["count"]
        
        return {
            "total_relationships": total_relationships,
            "unique_pages": len(unique_pages),
            "unique_endpoints": len(unique_endpoints),
            "by_api_version": version_counts
        }

