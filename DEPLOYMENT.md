# Lambda Documentation API Deployment Guide

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **SAM CLI** installed (see [logs.api README](../logs.api/README.md) for installation)
3. **Docker** installed and running (for SAM builds)
4. **MongoDB** accessible from Lambda
5. **S3 Bucket** created and accessible

## Pre-Deployment Checklist

- [ ] MongoDB connection URI configured
- [ ] S3 bucket name configured
- [ ] AWS credentials configured
- [ ] API key generated and secured
- [ ] Environment variables reviewed in `template.yaml`

## Deployment Steps

### 1. Configure Environment Variables

Update `samconfig.toml` with your actual values:

```toml
parameter_overrides = [
    "ApiKey=your-actual-api-key-here",
    "MongodbUri=mongodb://user:password@host:port",
    "S3BucketName=your-s3-bucket-name",
    "AwsRegion=us-east-1"
]
```

### 2. Build the Application

```bash
cd lambda/documentation.api
make sam-build
# or
sam build --use-container
```

### 3. Validate Template

```bash
make sam-validate
# or
sam validate --lint
```

### 4. Deploy to AWS

**First time (guided):**
```bash
sam deploy --guided
```

**Subsequent deployments:**
```bash
make sam-deploy
# or
sam deploy
```

### 5. Get API URL

After deployment, get the API Gateway URL:

```bash
sam list stack-outputs --stack-name documentation-api-stack
```

Look for `DocumentationApiUrl` in the outputs.

### 6. Update Appointment360 Configuration

Update `appointment360/app/core/config.py` or environment variables:

```bash
LAMBDA_DOCUMENTATION_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
LAMBDA_DOCUMENTATION_API_KEY=your-api-key-here
```

## Testing Deployment

### Health Check

```bash
curl https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/health
```

### Test Endpoint (with API key)

```bash
curl -X GET \
  https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/docs \
  -H "X-API-Key: your-api-key-here"
```

## Monitoring

### View Lambda Logs

```bash
make sam-logs
# or
sam logs -n DocumentationApiFunction --stack-name documentation-api-stack --tail
```

### CloudWatch Metrics

Monitor in AWS CloudWatch:
- Lambda invocations
- Error rates
- Duration
- API Gateway requests

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MongoDB URI in `template.yaml`
   - Verify network connectivity from Lambda
   - Check security groups/VPC configuration

2. **S3 Access Denied**
   - Verify IAM role has S3 permissions
   - Check bucket name and region
   - Verify bucket exists

3. **API Key Authentication Failed**
   - Verify API key matches in `template.yaml` and appointment360 config
   - Check `X-API-Key` header is being sent

4. **Timeout Errors**
   - Increase Lambda timeout in `template.yaml`
   - Check MongoDB connection pool settings
   - Monitor CloudWatch for slow queries

## Rollback

If deployment fails or issues occur:

```bash
sam delete --stack-name documentation-api-stack
```

Then redeploy with corrected configuration.

## Post-Deployment

1. Update appointment360 with new Lambda URL
2. Test all endpoints from appointment360
3. Monitor logs for errors
4. Verify S3 uploads/downloads working
5. Test presigned URL generation
