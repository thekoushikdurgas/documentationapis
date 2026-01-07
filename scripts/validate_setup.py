#!/usr/bin/env python3
"""Validate Lambda documentation API setup before deployment."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    exists = path.exists()
    if not exists:
        print(f"❌ {description}: {filepath} not found")
    else:
        print(f"✅ {description}: {filepath}")
    return exists

def check_import(module: str, description: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module)
        print(f"✅ {description}: {module}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module} - {e}")
        return False

def check_env_var(var: str, description: str, required: bool = False) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(var)
    if not value:
        if required:
            print(f"❌ {description}: {var} not set (REQUIRED)")
            return False
        else:
            print(f"⚠️  {description}: {var} not set (optional)")
            return True
    else:
        # Mask sensitive values
        masked = value[:8] + "..." if len(value) > 8 else "***"
        print(f"✅ {description}: {var} = {masked}")
        return True

def main():
    """Run validation checks."""
    print("=" * 60)
    print("Lambda Documentation API - Setup Validation")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    # Check core files
    print("📁 Core Files:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/main.py", "Main application")
    all_checks_passed &= check_file_exists("app/core/config.py", "Configuration")
    all_checks_passed &= check_file_exists("app/core/exceptions.py", "Exceptions")
    all_checks_passed &= check_file_exists("template.yaml", "SAM template")
    all_checks_passed &= check_file_exists("requirements.txt", "Requirements")
    all_checks_passed &= check_file_exists("samconfig.toml", "SAM config")
    print()
    
    # Check services
    print("🔧 Services:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/services/documentation_service.py", "Documentation service")
    all_checks_passed &= check_file_exists("app/services/endpoint_documentation_service.py", "Endpoint service")
    all_checks_passed &= check_file_exists("app/services/documentation_relationship_service.py", "Relationship service")
    all_checks_passed &= check_file_exists("app/services/s3_service.py", "S3 service")
    print()
    
    # Check repositories
    print("💾 Repositories:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/repositories/documentation_repository.py", "Documentation repository")
    all_checks_passed &= check_file_exists("app/repositories/endpoint_documentation_repository.py", "Endpoint repository")
    all_checks_passed &= check_file_exists("app/repositories/page_endpoint_relationship_repository.py", "Relationship repository")
    print()
    
    # Check API endpoints
    print("🌐 API Endpoints:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/api/v1/endpoints/documentation.py", "Documentation endpoints")
    all_checks_passed &= check_file_exists("app/api/v1/endpoints/endpoint_documentation.py", "Endpoint documentation endpoints")
    all_checks_passed &= check_file_exists("app/api/v1/endpoints/documentation_relationships.py", "Relationship endpoints")
    all_checks_passed &= check_file_exists("app/api/v1/router.py", "API router")
    print()
    
    # Check infrastructure
    print("🏗️  Infrastructure:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/clients/mongodb.py", "MongoDB client")
    all_checks_passed &= check_file_exists("app/api/dependencies.py", "API dependencies")
    all_checks_passed &= check_file_exists("app/middleware/compression.py", "Compression middleware")
    all_checks_passed &= check_file_exists("app/middleware/monitoring.py", "Monitoring middleware")
    print()
    
    # Check utilities
    print("🛠️  Utilities:")
    print("-" * 60)
    all_checks_passed &= check_file_exists("app/utils/logger.py", "Logger")
    all_checks_passed &= check_file_exists("app/utils/lambda_utils.py", "Lambda utils")
    all_checks_passed &= check_file_exists("app/utils/background_tasks.py", "Background tasks")
    print()
    
    # Check Python imports
    print("🐍 Python Imports:")
    print("-" * 60)
    try:
        from app.core.config import get_settings
        print("✅ Configuration import")
    except Exception as e:
        print(f"❌ Configuration import: {e}")
        all_checks_passed = False
    
    try:
        from app.main import app
        print("✅ FastAPI app import")
    except Exception as e:
        print(f"❌ FastAPI app import: {e}")
        all_checks_passed = False
    
    try:
        from app.api.v1.router import api_router
        print("✅ API router import")
    except Exception as e:
        print(f"❌ API router import: {e}")
        all_checks_passed = False
    print()
    
    # Check environment variables (optional for local dev)
    print("🔐 Environment Variables (for local development):")
    print("-" * 60)
    check_env_var("API_KEY", "API Key", required=False)
    check_env_var("MONGODB_URI", "MongoDB URI", required=False)
    check_env_var("S3_BUCKET_NAME", "S3 Bucket Name", required=False)
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("✅ All file checks passed!")
        print()
        print("Next steps:")
        print("1. Review samconfig.toml and update with your values")
        print("2. Run: sam build --use-container")
        print("3. Run: sam validate --lint")
        print("4. Run: sam deploy --guided")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
