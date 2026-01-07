"""Test MongoDB connection for documentation API."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.mongodb import (
    get_mongodb_database,
    close_mongodb_connection,
    check_mongodb_health,
    is_mongodb_client_initialized
)
from app.core.config import get_settings
from app.repositories.documentation_repository import DocumentationRepository

settings = get_settings()


async def test_connection():
    """Test MongoDB connection and verify database/collection access."""
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Display configuration
    print("\n📋 Configuration:")
    mongodb_uri_display = settings.MONGODB_URI
    if mongodb_uri_display and len(mongodb_uri_display) > 50:
        # Mask credentials in URI for security
        if "@" in mongodb_uri_display:
            parts = mongodb_uri_display.split("@")
            if len(parts) == 2:
                creds_part = parts[0]
                rest = parts[1]
                if "//" in creds_part:
                    protocol = creds_part.split("//")[0] + "//"
                    creds = creds_part.split("//")[1]
                    if ":" in creds:
                        user = creds.split(":")[0]
                        mongodb_uri_display = f"{protocol}{user}:***@{rest}"
        else:
            mongodb_uri_display = mongodb_uri_display[:50] + "..."
    print(f"  MongoDB URI: {mongodb_uri_display or 'Not set'}")
    print(f"  Database: {settings.MONGODB_DB_NAME}")
    print(f"  Max Pool Size: {settings.MONGODB_MAX_POOL_SIZE}")
    print(f"  Min Pool Size: {settings.MONGODB_MIN_POOL_SIZE}")
    
    try:
        # Test 1: Basic connection
        print("\n🔌 Test 1: Connecting to MongoDB...")
        db = await get_mongodb_database()
        print(f"  ✅ Connected to database: {db.name}")
        
        # Test 2: Collection access
        print("\n📋 Test 2: Accessing documentation_pages collection...")
        repository = DocumentationRepository()
        collection = await repository._get_collection()
        print(f"  ✅ Collection '{repository.COLLECTION_NAME}' accessible")
        
        # Test 3: Count documents
        print("\n📊 Test 3: Counting documents...")
        count = await collection.count_documents({})
        print(f"  ✅ Found {count} document(s) in collection")
        
        # Test 4: Health check
        print("\n🏥 Test 4: Health check...")
        is_healthy = await check_mongodb_health()
        if is_healthy:
            print("  ✅ MongoDB health check passed")
        else:
            print("  ⚠️  MongoDB health check failed")
        
        # Test 5: Client initialization status
        print("\n🔧 Test 5: Client status...")
        is_initialized = is_mongodb_client_initialized()
        print(f"  ✅ Client initialized: {is_initialized}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("❌ Connection test failed!")
        print("=" * 60)
        print("\n💡 Troubleshooting:")
        print("  1. Check MONGODB_URI environment variable")
        print("  2. Verify MongoDB server is running")
        print("  3. Check network connectivity")
        print("  4. Verify credentials are correct")
        print("  5. Check MongoDB connection string format")
        print("  6. Ensure database user has proper permissions")
        
        return False
    finally:
        await close_mongodb_connection()
        print("\n✅ Connection closed")


if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
