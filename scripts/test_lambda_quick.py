#!/usr/bin/env python3
"""Quick test script for Lambda API without user input."""

import asyncio
import os
import sys
from pathlib import Path

import httpx

API_URL = "https://ostltf6zr0.execute-api.us-east-1.amazonaws.com"
API_KEY = "bc7a0177de676a8e8bd98c2a0e6f96152b7b1ae1e72eb3d108ed13d5f01fd9bd"

async def test_health():
    """Test health endpoint."""
    print("1. Testing /health endpoint...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data.get('status')}")
                print(f"   ✅ Database: {data.get('database')}")
                print(f"   ✅ Diagnostics: {data.get('diagnostics', {})}")
                return True
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

async def test_root():
    """Test root endpoint."""
    print("\n2. Testing / endpoint...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Service: {data.get('service')}")
                print(f"   ✅ Version: {data.get('version')}")
                return True
            else:
                print(f"   ❌ Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

async def test_public_endpoint():
    """Test public endpoint without auth."""
    print("\n3. Testing /docs (public, no auth)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/docs")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: 200")
                print(f"   ✅ Total pages: {data.get('total', 0)}")
                return True
            else:
                print(f"   ❌ Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

async def test_protected_no_auth():
    """Test protected endpoint without API key."""
    print("\n4. Testing /endpoint-docs without API key (should fail)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/endpoint-docs")
            if response.status_code == 401:
                print(f"   ✅ Status: 401 (authentication required)")
                return True
            else:
                print(f"   ⚠️  Status: {response.status_code} (expected 401)")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

async def test_protected_with_auth():
    """Test protected endpoint with API key."""
    print("\n5. Testing /endpoint-docs with API key...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{API_URL}/endpoint-docs",
                headers={"X-API-Key": API_KEY}
            )
            if response.status_code in [200, 404]:  # 404 is OK if no endpoints exist
                print(f"   ✅ Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Total endpoints: {data.get('total', 0)}")
                return True
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Lambda Documentation API - Quick Verification")
    print("=" * 60)
    print(f"\nAPI URL: {API_URL}\n")
    
    results = []
    results.append(await test_health())
    results.append(await test_root())
    results.append(await test_public_endpoint())
    results.append(await test_protected_no_auth())
    results.append(await test_protected_with_auth())
    
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
