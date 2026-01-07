"""Repository for endpoint documentation operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from app.clients.mongodb import get_mongodb_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EndpointDocumentationRepository:
    """Repository for endpoint documentation operations in MongoDB."""
    
    COLLECTION_NAME = "endpoint_documentations"
    
    def __init__(self):
        """Initialize repository."""
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """Get MongoDB collection, creating connection if needed."""
        if self._collection is None:
            db = await get_mongodb_database()
            self._collection = db[self.COLLECTION_NAME]
            # Create indexes
            await self._collection.create_index("endpoint_id", unique=True)
            await self._collection.create_index([("endpoint_path", 1), ("method", 1)], unique=True)
            await self._collection.create_index("api_version")
        return self._collection
    
    async def get_by_endpoint_id(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get endpoint documentation by endpoint_id."""
        collection = await self._get_collection()
        
        endpoint = await collection.find_one({"endpoint_id": endpoint_id})
        if endpoint:
            endpoint["_id"] = str(endpoint["_id"])
        return endpoint
    
    async def get_by_path_and_method(
        self,
        endpoint_path: str,
        method: str
    ) -> Optional[Dict[str, Any]]:
        """Get endpoint documentation by path and method."""
        collection = await self._get_collection()
        
        endpoint = await collection.find_one({
            "endpoint_path": endpoint_path,
            "method": method
        })
        if endpoint:
            endpoint["_id"] = str(endpoint["_id"])
        return endpoint
    
    async def list_all(
        self,
        filters: Optional[Dict] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all endpoints with optional filters."""
        collection = await self._get_collection()
        
        query = filters or {}
        
        cursor = collection.find(query).skip(offset).limit(limit).sort("endpoint_path", 1)
        endpoints = await cursor.to_list(length=limit)
        
        for endpoint in endpoints:
            endpoint["_id"] = str(endpoint["_id"])
        
        return endpoints
    
    async def count(self, filters: Optional[Dict] = None) -> int:
        """Count endpoints matching filters."""
        collection = await self._get_collection()
        
        query = filters or {}
        return await collection.count_documents(query)
    
    async def create_endpoint(self, endpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create endpoint documentation."""
        collection = await self._get_collection()
        
        result = await collection.insert_one(endpoint_data)
        endpoint_data["_id"] = str(result.inserted_id)
        
        return endpoint_data
    
    async def update_endpoint(
        self,
        endpoint_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update endpoint documentation."""
        collection = await self._get_collection()
        
        result = await collection.update_one(
            {"endpoint_id": endpoint_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Endpoint documentation '{endpoint_id}' not found")
        
        # Return updated document
        updated = await self.get_by_endpoint_id(endpoint_id)
        return updated
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete endpoint documentation."""
        collection = await self._get_collection()
        
        result = await collection.delete_one({"endpoint_id": endpoint_id})
        return result.deleted_count > 0

