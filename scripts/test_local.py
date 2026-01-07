#!/usr/bin/env python3
"""Test Lambda documentation API locally before deployment."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.core.config import get_settings

async def test_health_check():
    """Test health check endpoint."""
    print("Testing health check endpoint...")
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=5.0) as client:
        try:
            response = await client.get("/health")
            print(f"✅ Health check: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_root_endpoint():
    """Test root endpoint."""
    print("\nTesting root endpoint...")
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=5.0) as client:
        try:
            response = await client.get("/")
            print(f"✅ Root endpoint: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
            return False

async def test_list_pages():
    """Test list pages endpoint (public, no auth)."""
    print("\nTesting list pages endpoint...")
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=5.0) as client:
        try:
            response = await client.get("/docs")
            print(f"✅ List pages: {response.status_code}")
            data = response.json()
            print(f"   Total pages: {data.get('total', 0)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ List pages failed: {e}")
            return False

async def test_api_key_auth():
    """Test API key authentication."""
    print("\nTesting API key authentication...")
    settings = get_settings()
    api_key = settings.API_KEY
    
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=5.0) as client:
        # Test without API key (should fail for protected endpoints)
        try:
            response = await client.get("/endpoint-docs")
            if response.status_code == 401:
                print("✅ API key protection working (401 for missing key)")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Auth test: {e}")
        
        # Test with API key
        try:
            response = await client.get(
                "/endpoint-docs",
                headers={"X-API-Key": api_key}
            )
            print(f"✅ API key auth: {response.status_code}")
            return response.status_code in [200, 404]  # 404 is OK if no endpoints exist
        except Exception as e:
            print(f"❌ API key auth failed: {e}")
            return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Lambda Documentation API - Local Testing")
    print("=" * 60)
    print()
    print("Make sure the server is running:")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload")
    print()
    
    results = []
    
    try:
        results.append(await test_health_check())
        results.append(await test_root_endpoint())
        results.append(await test_list_pages())
        results.append(await test_api_key_auth())
    except httpx.ConnectError:
        print("❌ Could not connect to server. Is it running?")
        print("   Start with: uvicorn app.main:app --host 0.0.0.0 --port 8080")
        sys.exit(1)
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
