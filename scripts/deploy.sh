#!/bin/bash
# Deployment script for Lambda Documentation API

set -e

echo "=========================================="
echo "Lambda Documentation API Deployment"
echo "=========================================="

# Check prerequisites
echo "Checking prerequisites..."
command -v sam >/dev/null 2>&1 || { echo "SAM CLI not found. Please install it first." >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "AWS CLI not found. Please install it first." >&2; exit 1; }

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity >/dev/null 2>&1 || { echo "AWS credentials not configured. Run 'aws configure' first." >&2; exit 1; }

# Build
echo ""
echo "Building application..."
sam build --use-container

# Validate
echo ""
echo "Validating template..."
sam validate --lint

# Deploy
echo ""
echo "Deploying to AWS..."
echo "This will create/update the CloudFormation stack: documentation-api-stack"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Deployment cancelled."
    exit 1
fi

sam deploy

# Get outputs
echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Getting stack outputs..."
sam list stack-outputs --stack-name documentation-api-stack

echo ""
echo "Next steps:"
echo "1. Copy the DocumentationApiUrl from outputs above"
echo "2. Update appointment360/.env with:"
echo "   LAMBDA_DOCUMENTATION_API_URL=<DocumentationApiUrl>"
echo "   LAMBDA_DOCUMENTATION_API_KEY=<your-api-key>"
echo "3. Deploy appointment360 with updated configuration"
