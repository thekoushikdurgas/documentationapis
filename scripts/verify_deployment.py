#!/usr/bin/env python3
"""Verify Lambda documentation API deployment after AWS deployment."""

import asyncio
import os
import sys
from pathlib import Path

import httpx

def get_api_url():
    """Get API URL from environment or user input."""
    api_url = os.getenv("LAMBDA_DOCUMENTATION_API_URL")
    if not api_url:
        api_url = input("Enter Lambda API URL (from deployment output): ").strip()
        if not api_url:
            print("❌ API URL is required")
            sys.exit(1)
    # Remove trailing slash
    api_url = api_url.rstrip("/")
    return api_url

def get_api_key():
    """Get API key from environment or user input."""
    api_key = os.getenv("LAMBDA_DOCUMENTATION_API_KEY")
    if not api_key:
        api_key = input("Enter API key: ").strip()
        if not api_key:
            print("⚠️  API key not provided. Some tests will be skipped.")
    return api_key

async def test_health_check(api_url: str):
    """Test health check endpoint."""
    print("\n1. Testing health check endpoint...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data.get('status')}")
                print(f"   ✅ Database: {data.get('database')}")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

async def test_root_endpoint(api_url: str):
    """Test root endpoint."""
    print("\n2. Testing root endpoint...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Service: {data.get('service')}")
                print(f"   ✅ Version: {data.get('version')}")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

async def test_list_pages(api_url: str):
    """Test list pages endpoint (public, no auth)."""
    print("\n3. Testing list pages endpoint (public)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/docs")
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                print(f"   ✅ Status: 200")
                print(f"   ✅ Total pages: {total}")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

async def test_api_key_auth(api_url: str, api_key: str):
    """Test API key authentication."""
    if not api_key:
        print("\n4. Testing API key authentication...")
        print("   ⚠️  Skipped (no API key provided)")
        return None
    
    print("\n4. Testing API key authentication...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test without API key (should fail for protected endpoints)
        try:
            response = await client.get(f"{api_url}/endpoint-docs")
            if response.status_code == 401:
                print("   ✅ API key protection working (401 for missing key)")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Auth test: {e}")
        
        # Test with API key
        try:
            response = await client.get(
                f"{api_url}/endpoint-docs",
                headers={"X-API-Key": api_key}
            )
            if response.status_code in [200, 404]:  # 404 is OK if no endpoints exist
                print(f"   ✅ API key auth working (status: {response.status_code})")
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

async def test_cors(api_url: str):
    """Test CORS headers."""
    print("\n5. Testing CORS headers...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.options(
                f"{api_url}/docs",
                headers={"Origin": "https://example.com"}
            )
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
            }
            if cors_headers["access-control-allow-origin"]:
                print(f"   ✅ CORS enabled")
                return True
            else:
                print(f"   ⚠️  CORS headers not found")
                return False
        except Exception as e:
            print(f"   ⚠️  CORS test: {e}")
            return False

async def test_response_time(api_url: str):
    """Test response time."""
    print("\n6. Testing response time...")
    import time
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            start = time.time()
            response = await client.get(f"{api_url}/health")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            if response.status_code == 200:
                print(f"   ✅ Response time: {elapsed:.2f}ms")
                if elapsed < 1000:
                    print("   ✅ Performance: Good")
                elif elapsed < 3000:
                    print("   ⚠️  Performance: Acceptable")
                else:
                    print("   ⚠️  Performance: Slow")
                return True
            else:
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

async def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Lambda Documentation API - Deployment Verification")
    print("=" * 60)
    
    api_url = get_api_url()
    api_key = get_api_key()
    
    print(f"\nAPI URL: {api_url}")
    if api_key:
        print(f"API Key: {api_key[:8]}...")
    print()
    
    results = []
    
    try:
        results.append(await test_health_check(api_url))
        results.append(await test_root_endpoint(api_url))
        results.append(await test_list_pages(api_url))
        auth_result = await test_api_key_auth(api_url, api_key)
        if auth_result is not None:
            results.append(auth_result)
        results.append(await test_cors(api_url))
        results.append(await test_response_time(api_url))
    except httpx.ConnectError:
        print("\n❌ Could not connect to API. Check:")
        print("   1. API URL is correct")
        print("   2. Lambda is deployed and running")
        print("   3. API Gateway is configured correctly")
        print("   4. Network connectivity")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    passed = sum(1 for r in results if r is True)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(r for r in results if r is not None):
        print("✅ Deployment verification successful!")
        print("\nNext steps:")
        print("1. Update appointment360/.env with:")
        print(f"   LAMBDA_DOCUMENTATION_API_URL={api_url}")
        if api_key:
            print(f"   LAMBDA_DOCUMENTATION_API_KEY={api_key}")
        print("2. Deploy appointment360")
        print("3. Test integration from appointment360")
    else:
        print("⚠️  Some tests failed. Review the output above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
