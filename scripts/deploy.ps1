# Deployment script for Lambda Documentation API (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Lambda Documentation API Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow
try {
    sam --version | Out-Null
} catch {
    Write-Host "SAM CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

try {
    aws --version | Out-Null
} catch {
    Write-Host "AWS CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Build
Write-Host "`nBuilding application..." -ForegroundColor Yellow
sam build --use-container

# Validate
Write-Host "`nValidating template..." -ForegroundColor Yellow
sam validate --lint

# Deploy
Write-Host "`nDeploying to AWS..." -ForegroundColor Yellow
Write-Host "This will create/update the CloudFormation stack: documentation-api-stack" -ForegroundColor Yellow
$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 1
}

sam deploy

# Get outputs
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Getting stack outputs..." -ForegroundColor Yellow
sam list stack-outputs --stack-name documentation-api-stack

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy the DocumentationApiUrl from outputs above"
Write-Host "2. Update appointment360/.env with:"
Write-Host "   LAMBDA_DOCUMENTATION_API_URL=<DocumentationApiUrl>"
Write-Host "   LAMBDA_DOCUMENTATION_API_KEY=<your-api-key>"
Write-Host "3. Deploy appointment360 with updated configuration"
