# Quick Start Guide

## Local Development

### 1. Setup Environment

```bash
cd lambda/documentation.api

# Copy environment template
cp .env.example .env

# Edit .env with your values:
# - API_KEY (generate a secure key)
# - MONGODB_URI (your MongoDB connection string)
# - S3_BUCKET_NAME (your S3 bucket name)
# - AWS credentials (or use IAM role)
```

### 2. Install Dependencies

```bash
make install
# or
pip install -r requirements.txt
```

### 3. Run Locally

```bash
make run
# or
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`

### 4. Test Endpoints

```bash
# Health check (no auth)
curl http://localhost:8080/health

# List pages (no auth)
curl http://localhost:8080/docs

# Create page (requires API key)
curl -X POST http://localhost:8080/docs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "page_id": "test_page",
    "metadata": {
      "route": "/test",
      "purpose": "Test page"
    },
    "content": "# Test Content"
  }'
```

## AWS Lambda Deployment

### 1. Prerequisites

- AWS CLI configured (`aws configure`)
- SAM CLI installed
- Docker running (for builds)

### 2. Configure Deployment

Edit `samconfig.toml` with your values:

```toml
parameter_overrides = [
    "ApiKey=your-actual-api-key",
    "MongodbUri=mongodb://user:pass@host:port",
    "S3BucketName=your-bucket-name",
    "AwsRegion=us-east-1"
]
```

### 3. Deploy

**Using Makefile:**
```bash
make sam-build
make sam-deploy
```

**Using Scripts:**
```bash
# Linux/macOS
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Windows
.\scripts\deploy.ps1
```

**Manual:**
```bash
sam build --use-container
sam deploy --guided  # First time
sam deploy           # Subsequent
```

### 4. Get API URL

```bash
sam list stack-outputs --stack-name documentation-api-stack
```

Copy the `DocumentationApiUrl` value.

### 5. Update Appointment360

Add to `appointment360/.env`:

```bash
LAMBDA_DOCUMENTATION_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
LAMBDA_DOCUMENTATION_API_KEY=your-api-key
```

## Testing

### Run Tests

```bash
# Lambda tests
cd lambda/documentation.api
pytest tests/ -v

# Appointment360 tests
cd appointment360
pytest tests/services/test_lambda_documentation_client.py -v
```

### Integration Testing

1. Deploy Lambda
2. Update appointment360 config
3. Test endpoints from appointment360:
   ```bash
   curl http://localhost:8000/api/v4/docs
   ```

## Troubleshooting

### Lambda Connection Issues

- Check `LAMBDA_DOCUMENTATION_API_URL` is correct
- Verify API key matches in both services
- Check network connectivity

### S3 Issues

- Verify bucket exists and is accessible
- Check IAM role has S3 permissions
- Verify bucket name in configuration

### MongoDB Issues

- Check MongoDB URI is correct
- Verify network connectivity from Lambda
- Check security groups/VPC configuration

## Next Steps

1. Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guide
2. Review [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for architecture overview
3. See [README.md](README.md) for API documentation
