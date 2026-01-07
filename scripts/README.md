# Lambda Documentation API Scripts

This directory contains utility scripts for development and deployment.

## Scripts

### `validate_setup.py`

Validates that all required files and dependencies are in place before deployment.

**Usage:**
```bash
python scripts/validate_setup.py
# or
make validate
```

**What it checks:**
- Core application files (main.py, config.py, etc.)
- Service files (documentation_service.py, etc.)
- Repository files
- API endpoint files
- Infrastructure files (MongoDB client, middleware, etc.)
- Utility files
- Python imports
- Environment variables (optional)

### `test_mongo_connection.py`

Tests MongoDB connection for the documentation API.

**Usage:**
```bash
# Set environment variables (or use .env file)
export MONGODB_URI="mongodb://admin:password@host:27017"
export MONGODB_DB_NAME="documentation"
export S3_BUCKET_NAME="contact360-bucket"

# Run test
python scripts/test_mongo_connection.py
```

**What it tests:**
- MongoDB connection
- Database access
- Collection access (documentation_pages)
- Document count
- Health check
- Client initialization status

**Required Environment Variables:**
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB_NAME` - Database name (default: "documentation")
- `S3_BUCKET_NAME` - S3 bucket name for documentation storage

**Output:**
- Connection status for each test
- Document count in collection
- Troubleshooting tips on failure

### `test_s3_connection.py`

Tests S3 bucket connectivity and access for the documentation API.

**Usage:**
```bash
# Set environment variables (or use .env file)
export S3_BUCKET_NAME="contact360-bucket"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Run test
python scripts/test_s3_connection.py
```

**What it tests:**
- AWS credentials configuration
- Bucket existence check
- Bucket creation capability (if bucket doesn't exist)
- Read access (listing objects)
- Write access (uploading test file)
- Presigned URL generation
- Proper cleanup of test files

**Required Environment Variables:**
- `S3_BUCKET_NAME` - S3 bucket name for documentation storage
- `AWS_ACCESS_KEY_ID` - AWS access key (or use IAM role/default credentials)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (or use IAM role/default credentials)
- `AWS_REGION` - AWS region where bucket is/will be located (default: "us-east-1")

**Output:**
- Configuration display (masked credentials)
- Bucket existence status
- Read/write permission verification
- Object listing (if any exist)
- Troubleshooting tips on failure
- Exit code: 0 for success, 1 for failure

**Example Output:**
```
============================================================
S3 Bucket Connection Test
============================================================

📋 Configuration:
  Bucket Name: contact360-bucket
  AWS Region: us-east-1
  Access Key ID: AKIAIOSFO...
  Secret Key: ✅ Configured
  S3 Prefix: documentation/

🔍 Test 1: Checking if bucket exists...
  ✅ Bucket 'contact360-bucket' exists and is accessible

📋 Test 2: Testing read access (listing objects)...
  ✅ Read access confirmed
  📊 Found 5 object(s) with prefix 'documentation/'

✍️  Test 3: Testing write access...
  ✅ Write access confirmed
  📝 Test file uploaded: documentation/_test_connection.txt
  🧹 Test file deleted (cleanup successful)

🔗 Test 4: Testing presigned URL generation...
  ✅ Presigned URL generation confirmed

============================================================
✅ All S3 connection tests passed!
============================================================
```

### `seed_documentation_pages.py`

Seeds documentation pages from markdown files into MongoDB and S3.

**Usage:**
```bash
# Set environment variables (or use .env file)
export MONGODB_URI="mongodb://admin:password@host:27017"
export MONGODB_DB_NAME="documentation"
export S3_BUCKET_NAME="contact360-bucket"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Run seeding
python scripts/seed_documentation_pages.py
```

**What it does:**
- Checks S3 bucket exists and creates it if missing
- Verifies MongoDB connection
- Reads markdown files from `frontent/docs/pages/`
- Parses metadata (Route, File, Authentication, Authorization, Purpose)
- Uploads content to S3
- Stores metadata in MongoDB
- Creates new pages or updates existing ones
- Shows progress and summary

**Required Environment Variables:**
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB_NAME` - Database name (default: "documentation")
- `S3_BUCKET_NAME` - S3 bucket name
- `AWS_ACCESS_KEY_ID` - AWS access key (or use IAM role in Lambda)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (or use IAM role in Lambda)
- `AWS_REGION` - AWS region (default: "us-east-1")

**Excluded Files:**
The script automatically excludes template and tracking files:
- `_page_docs_template.md`
- Files containing: `CSS_`, `DOCUMENTATION_`, `FINAL_`, `IMPLEMENTATION_`, `PROGRESS_`, `page_docs_coverage`, `sidebar_`

**Output:**
- Progress indicator showing which pages are being created/updated
- Summary with counts of created, updated, and error pages
- S3 bucket and prefix information
- Error details if any failures occur

**Example Output:**
```
============================================================
Documentation Pages Seeding Script
============================================================

📁 Found 53 documentation files to seed
📂 Directory: /path/to/frontent/docs/pages

✅ MongoDB connection successful

[  1/ 53] ➕ Creating: about_page
[  2/ 53] ➕ Creating: contacts_page
[  3/ 53] 🔄 Updating: dashboard_page
...

============================================================
Seeding Summary
============================================================
  ✅ Created:  45
  🔄 Updated:  8
  ❌ Errors:  0
  📄 Total:   53

  📦 S3 Bucket:  contact360-bucket
  📂 S3 Prefix:  documentation/
  🗄️  Database:   documentation
  📋 Collection: documentation_pages
============================================================
```

### `test_local.py`

Tests the API locally when running with `uvicorn`.

**Usage:**
```bash
# Terminal 1: Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Run tests
python scripts/test_local.py
# or
make test-local
```

**What it tests:**
- Health check endpoint (`/health`)
- Root endpoint (`/`)
- List pages endpoint (`/docs`) - public
- API key authentication

### `deploy.sh` (Linux/macOS)

Interactive deployment script for Linux/macOS.

**Usage:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**What it does:**
- Checks prerequisites (SAM CLI, AWS CLI, Docker)
- Validates AWS credentials
- Builds the application
- Validates the template
- Deploys to AWS
- Shows stack outputs

### `deploy.ps1` (Windows)

Interactive deployment script for Windows PowerShell.

**Usage:**
```powershell
.\scripts\deploy.ps1
```

**What it does:**
- Same as `deploy.sh` but for Windows

### `verify_deployment.py`

Verifies Lambda deployment after AWS deployment.

**Usage:**
```bash
# Set environment variables
export LAMBDA_DOCUMENTATION_API_URL="https://your-api-url.execute-api.us-east-1.amazonaws.com"
export LAMBDA_DOCUMENTATION_API_KEY="your-api-key"

# Run verification
python scripts/verify_deployment.py
# or
make verify-deployment
```

**What it tests:**
- Health check endpoint
- Root endpoint
- List pages endpoint (public)
- API key authentication
- CORS headers
- Response time

### `integration_test.sh`

Bash script for integration testing (alternative to Python script).

**Usage:**
```bash
chmod +x scripts/integration_test.sh
./scripts/integration_test.sh
```

**What it tests:**
- Health check
- Root endpoint
- List pages
- API key authentication
- Protected endpoint without key

## Running Scripts

All scripts should be run from the `lambda/documentation.api` directory:

```bash
cd lambda/documentation.api
python scripts/validate_setup.py
python scripts/test_mongo_connection.py
python scripts/seed_documentation_pages.py
```

Or use the Makefile commands:

```bash
make validate      # Run validation
make test-local    # Run local tests
```

## Environment Variables

For seeding scripts, create a `.env` file in the `lambda/documentation.api` directory:

```bash
# MongoDB
MONGODB_URI=mongodb://admin:password@host:27017
MONGODB_DB_NAME=documentation

# S3
S3_BUCKET_NAME=contact360-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# API (for testing)
API_KEY=your-api-key
```

## Troubleshooting

### MongoDB Connection Issues

1. **Connection refused**: Check if MongoDB server is running
2. **Authentication failed**: Verify credentials in MONGODB_URI
3. **Network timeout**: Check network connectivity and firewall rules
4. **Database not found**: Database will be created automatically on first use

**Solution:**
```bash
# Test connection first
python scripts/test_mongo_connection.py
```

### S3 Upload Issues

1. **Access denied**: Verify AWS credentials and IAM permissions
2. **Bucket not found**: Ensure S3 bucket exists in the specified region
3. **Region mismatch**: Check AWS_REGION matches bucket region

**Solution:**
- Verify AWS credentials: `aws s3 ls`
- Check bucket exists: `aws s3 ls s3://contact360-bucket`
- Verify IAM permissions for S3 upload

### Seeding Issues

1. **Markdown files not found**: Ensure `frontent/docs/pages/` directory exists relative to workspace root
   - Script looks for: `{workspace_root}/frontent/docs/pages/`
   - Check the path is correct

2. **Metadata parsing errors**: Check markdown file format matches expected structure
   - Required fields: `**Route:**`, `**File:**`, `**Authentication:**`, `**Purpose:**`
   - Optional field: `**Authorization:**`

3. **Page already exists**: Script will update existing pages automatically

**Solution:**
- Verify files exist: `ls frontent/docs/pages/*.md`
- Check markdown format matches template
- Review error messages in output for specific issues

### Common Errors

**Error: "Documentation directory not found"**
- Solution: Ensure `frontent/docs/pages/` exists relative to workspace root

**Error: "MongoDB connection failed"**
- Solution: Run `test_mongo_connection.py` to diagnose connection issues

**Error: "S3 upload failed" or "S3 bucket check failed"**
- Solution: Run `python scripts/test_s3_connection.py` to diagnose S3 issues
- Verify AWS credentials and bucket permissions
- Check S3_BUCKET_NAME is correct
- The seed script will attempt to create the bucket if it doesn't exist

**Error: "Page with page_id 'X' already exists"**
- Solution: This shouldn't happen - script checks and updates existing pages
- If it occurs, there may be a database constraint issue
