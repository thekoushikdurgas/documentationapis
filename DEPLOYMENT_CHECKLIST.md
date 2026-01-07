# Deployment Checklist

## Pre-Deployment

### Lambda Documentation API

- [ ] MongoDB accessible from Lambda (network/VPC configured)
- [ ] S3 bucket created and accessible
- [ ] AWS credentials configured (`aws configure`)
- [ ] SAM CLI installed and working
- [ ] Docker running (for SAM builds)
- [ ] API key generated and secured
- [ ] `samconfig.toml` updated with actual values:
  - [ ] `ApiKey` - Secure API key
  - [ ] `MongodbUri` - MongoDB connection string
  - [ ] `S3BucketName` - S3 bucket name
  - [ ] `AwsRegion` - AWS region

### Appointment360

- [ ] Lambda documentation API URL known (will be set after Lambda deployment)
- [ ] Lambda documentation API key matches Lambda configuration
- [ ] Environment variables ready to update

## Deployment Steps

### Step 1: Deploy Lambda

```bash
cd lambda/documentation.api

# Build
sam build --use-container

# Validate
sam validate --lint

# Deploy (first time - guided)
sam deploy --guided

# Or use script
./scripts/deploy.sh  # Linux/macOS
.\scripts\deploy.ps1  # Windows
```

**After deployment:**
- [ ] Copy `DocumentationApiUrl` from stack outputs
- [ ] Test health endpoint: `curl <DocumentationApiUrl>/health`
- [ ] Test list pages: `curl <DocumentationApiUrl>/docs`
- [ ] Verify Lambda logs show no errors

### Step 2: Update Appointment360 Configuration

Update `appointment360/.env` or deployment environment:

```bash
LAMBDA_DOCUMENTATION_API_URL=<DocumentationApiUrl from Step 1>
LAMBDA_DOCUMENTATION_API_KEY=<same as Lambda ApiKey>
LAMBDA_DOCUMENTATION_API_TIMEOUT=10
```

- [ ] Configuration updated
- [ ] API URL is correct (no trailing slash)
- [ ] API key matches Lambda configuration

### Step 3: Deploy Appointment360

- [ ] Appointment360 deployed with updated configuration
- [ ] Environment variables loaded correctly

### Step 4: Verify Integration

#### Test Public Endpoints (No Auth)

```bash
# List pages
curl http://appointment360-url/api/v4/docs

# Get page
curl http://appointment360-url/api/v4/docs/{page_id}

# Get content
curl http://appointment360-url/api/v4/docs/{page_id}/content
```

- [ ] List pages endpoint works
- [ ] Get page endpoint works
- [ ] Get content endpoint works (returns markdown)

#### Test Admin Endpoints (Requires Auth)

```bash
# Create page (requires admin JWT token)
curl -X POST http://appointment360-url/api/v4/docs \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

- [ ] Create page endpoint works
- [ ] Update page endpoint works
- [ ] Delete page endpoint works

#### Test Endpoint Documentation

```bash
# List endpoints (requires auth)
curl -X GET http://appointment360-url/api/v4/endpoint-docs \
  -H "Authorization: Bearer <jwt-token>"
```

- [ ] List endpoints works
- [ ] Get endpoint works
- [ ] Create/update/delete endpoints work

#### Test Relationships

```bash
# Get graph (requires auth)
curl -X GET http://appointment360-url/api/v4/docs/relationships/graph \
  -H "Authorization: Bearer <jwt-token>"
```

- [ ] Get graph works
- [ ] Get statistics works
- [ ] Sync relationships works

### Step 5: Monitor and Verify

- [ ] Check Lambda CloudWatch logs for errors
- [ ] Check appointment360 logs for Lambda client errors
- [ ] Verify S3 uploads are working (check bucket)
- [ ] Verify MongoDB operations (check database)
- [ ] Test presigned URL generation and access
- [ ] Monitor API Gateway metrics

## Rollback Plan

If issues occur:

1. **Lambda Issues:**
   ```bash
   sam delete --stack-name documentation-api-stack
   ```
   Then redeploy with fixes.

2. **Appointment360 Issues:**
   - Revert to previous deployment
   - Or temporarily disable Lambda integration (would require code changes)

## Post-Deployment

- [ ] All endpoints tested and working
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Team notified of changes

## Success Criteria

✅ Lambda deployed and accessible  
✅ All 22 endpoints working  
✅ Appointment360 successfully proxies to Lambda  
✅ S3 operations working  
✅ MongoDB operations working  
✅ No errors in logs  
✅ Performance acceptable  
