"""Test S3 bucket connection and access for documentation API."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.s3_service import S3Service
from app.core.config import get_settings
from app.core.exceptions import S3Error

settings = get_settings()


async def test_s3_connection():
    """Test S3 bucket connectivity and access."""
    print("=" * 60)
    print("S3 Bucket Connection Test")
    print("=" * 60)
    
    # Display configuration
    print("\n📋 Configuration:")
    aws_access_key_display = settings.AWS_ACCESS_KEY_ID
    if aws_access_key_display:
        aws_access_key_display = aws_access_key_display[:10] + "..." if len(aws_access_key_display) > 10 else aws_access_key_display
    else:
        aws_access_key_display = "Not set"
    
    aws_secret_display = "✅ Configured" if settings.AWS_SECRET_ACCESS_KEY else "❌ Not set"
    
    print(f"  Bucket Name: {settings.S3_BUCKET_NAME or 'Not set'}")
    print(f"  AWS Region: {settings.AWS_REGION}")
    print(f"  Access Key ID: {aws_access_key_display}")
    print(f"  Secret Key: {aws_secret_display}")
    print(f"  S3 Prefix: {settings.S3_DOCUMENTATION_PREFIX}")
    
    # Validate configuration
    if not settings.S3_BUCKET_NAME:
        print("\n❌ ERROR: S3_BUCKET_NAME is not configured")
        print("\n💡 Please set the S3_BUCKET_NAME environment variable")
        return False
    
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("\n⚠️  WARNING: AWS credentials not fully configured")
        print("   The script will attempt to use default AWS credentials (e.g., from AWS CLI)")
    
    s3_service = S3Service()
    
    try:
        # Test 1: Check if bucket exists
        print("\n🔍 Test 1: Checking if bucket exists...")
        try:
            bucket_exists = await s3_service.bucket_exists()
            if bucket_exists:
                print(f"  ✅ Bucket '{settings.S3_BUCKET_NAME}' exists and is accessible")
            else:
                print(f"  ⚠️  Bucket '{settings.S3_BUCKET_NAME}' does not exist")
                print("\n💡 Attempting to create bucket...")
                try:
                    created = await s3_service.create_bucket()
                    if created:
                        print(f"  ✅ Bucket '{settings.S3_BUCKET_NAME}' created successfully")
                    else:
                        print(f"  ❌ Failed to create bucket")
                        return False
                except S3Error as e:
                    print(f"  ❌ Failed to create bucket: {e}")
                    print("\n💡 Troubleshooting:")
                    print("  - Check IAM permissions for bucket creation")
                    print("  - Verify bucket name is valid and globally unique")
                    print("  - Ensure AWS_REGION is set correctly")
                    return False
        except S3Error as e:
            if "Access denied" in str(e):
                print(f"  ❌ Access denied to bucket '{settings.S3_BUCKET_NAME}'")
                print(f"     Error: {e}")
                print("\n💡 Troubleshooting:")
                print("  - Check IAM permissions for bucket access")
                print("  - Verify AWS credentials have s3:HeadBucket permission")
                print("  - Ensure bucket name is correct")
                return False
            else:
                print(f"  ❌ Error checking bucket: {e}")
                return False
        
        # Test 2: List objects in bucket (test read permission)
        print("\n📋 Test 2: Testing read access (listing objects)...")
        try:
            import aioboto3
            session = s3_service._get_session()
            async with session.client("s3") as s3_client:
                # List objects with prefix
                paginator = s3_client.get_paginator("list_objects_v2")
                object_count = 0
                async for page in paginator.paginate(
                    Bucket=settings.S3_BUCKET_NAME,
                    Prefix=settings.S3_DOCUMENTATION_PREFIX,
                    MaxKeys=10  # Limit to first 10 for testing
                ):
                    contents = page.get("Contents", [])
                    object_count += len(contents)
                    if contents:
                        print(f"  ✅ Read access confirmed")
                        print(f"  📊 Found {object_count} object(s) with prefix '{settings.S3_DOCUMENTATION_PREFIX}'")
                        # Show first few objects
                        for i, obj in enumerate(contents[:3], 1):
                            size_kb = obj.get("Size", 0) / 1024
                            print(f"     {i}. {obj.get('Key')} ({size_kb:.2f} KB)")
                        if len(contents) > 3:
                            print(f"     ... and {len(contents) - 3} more")
                        break
                else:
                    print(f"  ✅ Read access confirmed (bucket is empty or prefix has no objects)")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not list objects: {e}")
            print("  (This may indicate read permission issues)")
        
        # Test 3: Test write permission (upload a test file)
        print("\n✍️  Test 3: Testing write access...")
        try:
            test_key = f"{settings.S3_DOCUMENTATION_PREFIX}_test_connection.txt"
            test_content = b"Test connection file - can be safely deleted"
            
            await s3_service.upload_file(
                file_content=test_content,
                s3_key=test_key,
                content_type="text/plain"
            )
            print(f"  ✅ Write access confirmed")
            print(f"  📝 Test file uploaded: {test_key}")
            
            # Clean up: delete the test file
            try:
                await s3_service.delete_file(test_key)
                print(f"  🧹 Test file deleted (cleanup successful)")
            except Exception as cleanup_error:
                print(f"  ⚠️  Warning: Could not delete test file: {cleanup_error}")
                print(f"     Please manually delete: {test_key}")
        except S3Error as e:
            print(f"  ❌ Write access failed: {e}")
            print("\n💡 Troubleshooting:")
            print("  - Check IAM permissions for s3:PutObject")
            print("  - Verify bucket policy allows writes")
            return False
        except Exception as e:
            print(f"  ❌ Unexpected error during write test: {e}")
            return False
        
        # Test 4: Test presigned URL generation
        print("\n🔗 Test 4: Testing presigned URL generation...")
        try:
            # Create a temporary test file for URL generation
            test_url_key = f"{settings.S3_DOCUMENTATION_PREFIX}_test_url.txt"
            await s3_service.upload_file(
                file_content=b"Test URL file",
                s3_key=test_url_key,
                content_type="text/plain"
            )
            
            url = await s3_service.generate_presigned_url(test_url_key)
            print(f"  ✅ Presigned URL generation confirmed")
            print(f"  🔗 Generated URL (first 80 chars): {url[:80]}...")
            
            # Clean up
            await s3_service.delete_file(test_url_key)
        except Exception as e:
            print(f"  ⚠️  Warning: Presigned URL generation failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ All S3 connection tests passed!")
        print("=" * 60)
        print(f"\n📦 Bucket: {settings.S3_BUCKET_NAME}")
        print(f"🌍 Region: {settings.AWS_REGION}")
        print(f"📂 Prefix: {settings.S3_DOCUMENTATION_PREFIX}")
        return True
        
    except S3Error as e:
        print(f"\n❌ S3 Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("❌ S3 connection test failed!")
        print("=" * 60)
        print("\n💡 Troubleshooting:")
        print("  1. Check S3_BUCKET_NAME environment variable")
        print("  2. Verify AWS credentials are configured")
        print("  3. Check AWS_REGION matches bucket region")
        print("  4. Verify IAM permissions for S3 access")
        print("  5. Ensure bucket exists or can be created")
        print("  6. Check network connectivity to AWS S3")
        
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("❌ Connection test failed!")
        print("=" * 60)
        print("\n💡 Troubleshooting:")
        print("  1. Check environment variables (S3_BUCKET_NAME, AWS_REGION)")
        print("  2. Verify AWS credentials")
        print("  3. Check Python dependencies (aioboto3, boto3)")
        print("  4. Verify network connectivity")
        
        return False


if __name__ == "__main__":
    result = asyncio.run(test_s3_connection())
    sys.exit(0 if result else 1)
