# Documentation API Service (FastAPI)

Centralized documentation microservice for Contact360 application.

## Overview

This service provides a RESTful API for managing documentation pages, endpoint documentation, and their relationships. It handles documentation storage in S3 (markdown content) and MongoDB (metadata), with presigned URLs for secure content access.

## Features

- **Documentation Pages CRUD**: Create, read, update, and delete documentation pages
- **S3 Storage**: Markdown content stored in S3 with presigned URLs
- **Endpoint Documentation**: Track and document API endpoints
- **Relationship Tracking**: Track relationships between pages and endpoints
- **MongoDB Integration**: Optimized Motor async client with connection pooling
- **API Key Authentication**: Secure endpoints with API key validation
- **Query Caching**: In-memory TTL cache for frequently accessed queries
- **Response Compression**: GZip compression for responses >1KB
- **Comprehensive Error Handling**: Custom exceptions with proper HTTP status codes

## API Endpoints

### Documentation Pages

- `GET /docs` - List all pages (public, no auth)
- `GET /docs/{page_id}` - Get page (public, no auth)
- `GET /docs/{page_id}/content` - Get content (public, no auth)
- `POST /docs` - Create page (admin, API key)
- `PUT /docs/{page_id}` - Update page (admin, API key)
- `DELETE /docs/{page_id}` - Delete page (admin, API key)
- `GET /docs/{page_id}/endpoints` - Get endpoints (public)
- `GET /docs/{page_id}/components` - Get components (public)
- `POST /docs/sync` - Sync from analysis (admin, API key)

### Endpoint Documentation

- `GET /endpoint-docs` - List endpoints (API key)
- `GET /endpoint-docs/{endpoint_id}` - Get endpoint (API key)
- `GET /endpoint-docs/{endpoint_id}/pages` - Get pages (API key)
- `POST /endpoint-docs` - Create endpoint (admin, API key)
- `PUT /endpoint-docs/{endpoint_id}` - Update endpoint (admin, API key)
- `DELETE /endpoint-docs/{endpoint_id}` - Delete endpoint (admin, API key)
- `POST /endpoint-docs/sync` - Sync from analysis (admin, API key)

### Relationships

- `GET /docs/relationships/graph` - Get graph (API key)
- `GET /docs/relationships/endpoint/{endpoint_path:path}` - Get pages (API key)
- `GET /docs/relationships/page/{page_path:path}` - Get endpoints (API key)
- `GET /docs/relationships/statistics` - Get stats (API key)
- `POST /docs/relationships/sync` - Sync relationships (admin, API key)
- `GET /docs/relationships/validate` - Validate (admin, API key)

### Health Check

- `GET /health` - Health check endpoint with MongoDB ping (no authentication required)
- `GET /` - Service information endpoint (no authentication required)

## Configuration

### Environment Variables

**Required:**

- `API_KEY` - Service authentication key
- `MONGODB_URI` - MongoDB connection string
- `S3_BUCKET_NAME` - S3 bucket name for documentation storage

**Optional (with defaults):**

- `MONGODB_DB_NAME` - Database name (default: "documentation")
- `PORT` - Server port (default: 8080, not used in Lambda)
- `LOG_LEVEL` - Logging level (default: INFO)
- `APP_ENV` - Environment (default: development)
- `S3_DOCUMENTATION_PREFIX` - S3 prefix (default: "documentation/")
- `S3_PRESIGNED_URL_EXPIRATION` - URL expiration in seconds (default: 3600)

## Authentication

The service uses API key authentication for service-to-service communication. Most endpoints require the `X-API-Key` header with a valid API key. Public endpoints (documentation pages listing and retrieval) do not require authentication.

### Example Request

```bash
curl -X POST http://localhost:8080/docs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key-here" \
  -d '{
    "page_id": "about_page",
    "metadata": {
      "route": "/about",
      "file_path": "app/about/page.tsx",
      "purpose": "About page"
    },
    "content": "# About\n\nThis is the about page."
  }'
```

## Running Locally

1. **Create `.env` file:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**

   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

3. **Run the service:**

   ```bash
   make run
   # or
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

## Deployment

### AWS Lambda (Recommended: SAM)

**Quick Start with SAM:**

1. **Install SAM CLI** (see logs.api README for instructions)

2. **Configure AWS credentials:**

   ```bash
   aws configure
   ```

3. **Build and deploy:**

   ```bash
   # First time (guided)
   sam build
   sam deploy --guided
   
   # Subsequent deployments
   make sam-build
   make sam-deploy
   ```

4. **Get API URL:**

   ```bash
   sam list stack-outputs --stack-name documentation-api-stack
   ```

**Using Makefile:**

```bash
make sam-build      # Build application
make sam-deploy     # Deploy to AWS
make sam-validate   # Validate template
make sam-local      # Test locally (http://localhost:3000)
make sam-logs       # View Lambda logs
make sam-delete     # Delete stack
```

## MongoDB Schema

Documentation pages are stored in the `documentation_pages` collection, endpoint documentation in `endpoint_documentations`, and relationships in `page_endpoint_relationships`.

## Development

### Install Dependencies

```bash
make install
```

### Run Tests

```bash
make test
```

### Lint Code

```bash
make lint
```

### Format Code

```bash
make format
```

### Clean Build Artifacts

```bash
make clean
```
