"""Documentation repository for MongoDB operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from app.clients.mongodb import get_mongodb_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentationRepository:
    """Repository for documentation page operations in MongoDB."""
    
    COLLECTION_NAME = "documentation_pages"
    
    def __init__(self):
        """Initialize repository."""
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """Get MongoDB collection, creating connection if needed."""
        if self._collection is None:
            db = await get_mongodb_database()
            self._collection = db[self.COLLECTION_NAME]
            # Create indexes on page_id and route for fast lookups
            await self._collection.create_index("page_id", unique=True)
            await self._collection.create_index("metadata.route")
        return self._collection
    
    async def get_by_page_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get documentation page by page_id."""
        collection = await self._get_collection()
        
        page = await collection.find_one({"page_id": page_id})
        if page:
            # Convert ObjectId to string for JSON serialization
            page["_id"] = str(page["_id"])
        return page
    
    async def get_by_route(self, route: str) -> Optional[Dict[str, Any]]:
        """Get documentation page by route."""
        collection = await self._get_collection()
        
        page = await collection.find_one({"metadata.route": route})
        if page:
            # Convert ObjectId to string for JSON serialization
            page["_id"] = str(page["_id"])
        return page
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """List all documentation pages sorted by route."""
        collection = await self._get_collection()
        
        cursor = collection.find({}).sort("metadata.route", 1)
        pages = await cursor.to_list(length=None)
        
        # Convert ObjectIds to strings
        for page in pages:
            page["_id"] = str(page["_id"])
        
        return pages
    
    async def create_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new documentation page."""
        collection = await self._get_collection()
        
        # Ensure metadata has required fields
        if "metadata" not in data:
            data["metadata"] = {}
        
        # Set timestamps
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()
        if "metadata" in data and "last_updated" not in data["metadata"]:
            data["metadata"]["last_updated"] = datetime.utcnow()
        
        # Check if page_id already exists
        existing = await self.get_by_page_id(data["page_id"])
        if existing:
            raise ValueError(f"Page with page_id '{data['page_id']}' already exists")
        
        result = await collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        return data
    
    async def update_page(
        self, 
        page_id: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update existing documentation page."""
        collection = await self._get_collection()
        
        # Remove _id if present (can't update MongoDB _id)
        update_data = {k: v for k, v in data.items() if k != "_id"}
        
        # Update last_updated timestamp in metadata
        if "metadata" in update_data:
            update_data["metadata"]["last_updated"] = datetime.utcnow()
            # Use dot notation to update nested metadata fields
            # This ensures we merge with existing metadata instead of replacing
            metadata_updates = {}
            for key, value in update_data["metadata"].items():
                metadata_updates[f"metadata.{key}"] = value
            # Remove metadata from update_data and add dot-notation updates
            del update_data["metadata"]
            update_data.update(metadata_updates)
        
        result = await collection.find_one_and_update(
            {"page_id": page_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["_id"] = str(result["_id"])
        return result
    
    async def delete_page(self, page_id: str) -> bool:
        """Delete documentation page."""
        collection = await self._get_collection()
        result = await collection.delete_one({"page_id": page_id})
        return result.deleted_count > 0

