# Documentation API Service - API Reference

## Base URL

**Production:** `https://ostltf6zr0.execute-api.us-east-1.amazonaws.com`  
**Local Development:** `http://localhost:8080`

## Authentication

The API uses API key authentication for service-to-service communication.

### Public Endpoints
- No authentication required
- Documentation pages listing and retrieval endpoints

### Protected Endpoints
- Require `X-API-Key` header
- All endpoint documentation and relationship endpoints
- All admin operations (create, update, delete, sync)

### Example Request with API Key

```bash
curl -X GET https://ostltf6zr0.execute-api.us-east-1.amazonaws.com/endpoint-docs \
  -H "X-API-Key: your-api-key-here"
```

## Response Format

All responses are JSON unless otherwise specified. Content endpoints return plain text markdown.

### Success Response

```json
{
  "page_id": "about_page",
  "metadata": {
    "route": "/about",
    "purpose": "About page"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "content_url": "https://s3.amazonaws.com/presigned-url",
  "content_url_expires_at": "2024-01-01T01:00:00Z"
}
```

### Error Response

```json
{
  "error": "DocumentationNotFoundError",
  "message": "Documentation page 'page_id' not found",
  "success": false
}
```

## Health Check Endpoints

### GET /health

Check service health and MongoDB connection status.

**Authentication:** Not required

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "diagnostics": {
    "client_initialized": true,
    "mongodb_uri_configured": true,
    "mongodb_db_name": "documentation",
    "s3_bucket_configured": true
  },
  "cache": {
    "cached": true,
    "stale": false,
    "age_seconds": 5,
    "last_checked": "2024-01-01T00:00:00Z"
  }
}
```

### GET /

Get service information.

**Authentication:** Not required

**Response:**
```json
{
  "service": "Documentation API Service",
  "version": "1.0.0",
  "status": "running"
}
```

## Documentation Pages Endpoints

### Public Endpoints

#### GET /docs

List all documentation pages.

**Authentication:** Not required

**Response:**
```json
{
  "pages": [
    {
      "_id": "123",
      "page_id": "about_page",
      "metadata": {
        "route": "/about",
        "purpose": "About page"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "content_url": "https://s3.amazonaws.com/presigned-url",
      "content_url_expires_at": "2024-01-01T01:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET /docs/{page_id}

Get documentation page by ID.

**Authentication:** Not required

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Response:**
```json
{
  "_id": "123",
  "page_id": "about_page",
  "metadata": {
    "route": "/about",
    "purpose": "About page",
    "s3_key": "documentation/about_page.md"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "content_url": "https://s3.amazonaws.com/presigned-url",
  "content_url_expires_at": "2024-01-01T01:00:00Z"
}
```

#### GET /docs/{page_id}/content

Get documentation page markdown content directly.

**Authentication:** Not required

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Response:** Plain text markdown

**Content-Type:** `text/markdown; charset=utf-8`

#### GET /docs/{page_id}/endpoints

Get all endpoints used by a page.

**Authentication:** Not required

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Response:**
```json
{
  "endpoints": [
    {
      "endpoint_path": "/api/v4/contacts",
      "method": "GET",
      "api_version": "v4"
    }
  ]
}
```

#### GET /docs/{page_id}/components

Get all components used by a page.

**Authentication:** Not required

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Response:**
```json
{
  "components": [
    {
      "name": "ContactForm",
      "file_path": "components/ContactForm.tsx"
    }
  ]
}
```

### Admin Endpoints

#### POST /docs

Create new documentation page.

**Authentication:** Required (API key)

**Request Body:**
```json
{
  "page_id": "about_page",
  "metadata": {
    "route": "/about",
    "file_path": "app/about/page.tsx",
    "purpose": "About page for the application",
    "authentication": "Not required",
    "authorization": null
  },
  "content": "# About\n\nThis is the about page content in markdown format."
}
```

**Response:** `201 Created`
```json
{
  "_id": "123",
  "page_id": "about_page",
  "metadata": {
    "route": "/about",
    "s3_key": "documentation/about_page.md"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "content_url": "https://s3.amazonaws.com/presigned-url",
  "content_url_expires_at": "2024-01-01T01:00:00Z"
}
```

#### PUT /docs/{page_id}

Update documentation page.

**Authentication:** Required (API key)

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Request Body:** (all fields optional)
```json
{
  "metadata": {
    "purpose": "Updated about page description"
  },
  "content": "# About\n\nUpdated content here."
}
```

**Response:**
```json
{
  "_id": "123",
  "page_id": "about_page",
  "metadata": {
    "route": "/about",
    "purpose": "Updated about page description",
    "s3_key": "documentation/about_page.md"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z",
  "content_url": "https://s3.amazonaws.com/presigned-url",
  "content_url_expires_at": "2024-01-01T02:00:00Z"
}
```

#### DELETE /docs/{page_id}

Delete documentation page.

**Authentication:** Required (API key)

**Path Parameters:**
- `page_id` (string, required): Unique page identifier

**Response:**
```json
{
  "success": true,
  "message": "Documentation page 'about_page' deleted successfully"
}
```

#### POST /docs/sync

Sync documentation pages from analysis data.

**Authentication:** Required (API key)

**Request Body:**
```json
{
  "pages": [
    {
      "page_path": "/about",
      "page_title": "About Page",
      "file_path": "app/about/page.tsx",
      "purpose": "About page"
    },
    {
      "page_path": "/contact",
      "page_title": "Contact Page",
      "file_path": "app/contact/page.tsx",
      "purpose": "Contact page"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synced 2 pages",
  "data": {
    "synced_count": 2,
    "created_count": 2,
    "updated_count": 0
  }
}
```

## Endpoint Documentation Endpoints

All endpoints require API key authentication.

### GET /endpoint-docs

List all endpoint documentation with optional filters.

**Authentication:** Required (API key)

**Query Parameters:**
- `api_version` (string, optional): Filter by API version (e.g., "v4")
- `method` (string, optional): Filter by HTTP method (e.g., "GET", "POST")
- `limit` (integer, optional): Maximum number of results (1-1000, default: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```
GET /endpoint-docs?api_version=v4&method=GET&limit=50&offset=0
```

**Response:**
```json
{
  "endpoints": [
    {
      "_id": "123",
      "endpoint_id": "get_contacts_v4",
      "endpoint_path": "/api/v4/contacts",
      "method": "GET",
      "api_version": "v4",
      "router_file": "app/api/v4/endpoints/contacts.py",
      "service_methods": ["list_contacts"],
      "repository_methods": ["get_all_contacts"],
      "authentication": "Bearer token (JWT)",
      "authorization": "User role required",
      "rate_limit": "100 requests/minute",
      "description": "List all contacts with filtering and pagination",
      "used_by_pages": [
        {
          "page_path": "/contacts",
          "page_title": "Contacts Page"
        }
      ],
      "page_count": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /endpoint-docs/{endpoint_id}

Get endpoint documentation by ID.

**Authentication:** Required (API key)

**Path Parameters:**
- `endpoint_id` (string, required): Unique endpoint identifier

**Response:**
```json
{
  "_id": "123",
  "endpoint_id": "get_contacts_v4",
  "endpoint_path": "/api/v4/contacts",
  "method": "GET",
  "api_version": "v4",
  "router_file": "app/api/v4/endpoints/contacts.py",
  "service_methods": ["list_contacts"],
  "repository_methods": ["get_all_contacts"],
  "authentication": "Bearer token (JWT)",
  "authorization": "User role required",
  "rate_limit": "100 requests/minute",
  "description": "List all contacts with filtering and pagination",
  "used_by_pages": [],
  "page_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### GET /endpoint-docs/{endpoint_id}/pages

Get all pages using a specific endpoint.

**Authentication:** Required (API key)

**Path Parameters:**
- `endpoint_id` (string, required): Unique endpoint identifier

**Response:**
```json
{
  "pages": [
    {
      "page_path": "/contacts",
      "page_title": "Contacts Page"
    }
  ]
}
```

### POST /endpoint-docs

Create endpoint documentation.

**Authentication:** Required (API key)

**Request Body:**
```json
{
  "endpoint_id": "get_contacts_v4",
  "endpoint_path": "/api/v4/contacts",
  "method": "GET",
  "api_version": "v4",
  "router_file": "app/api/v4/endpoints/contacts.py",
  "service_methods": ["list_contacts"],
  "repository_methods": ["get_all_contacts"],
  "authentication": "Bearer token (JWT)",
  "authorization": "User role required",
  "rate_limit": "100 requests/minute",
  "description": "List all contacts with filtering and pagination",
  "sql_file": null
}
```

**Response:** `201 Created`
```json
{
  "_id": "123",
  "endpoint_id": "get_contacts_v4",
  "endpoint_path": "/api/v4/contacts",
  "method": "GET",
  "api_version": "v4",
  "router_file": "app/api/v4/endpoints/contacts.py",
  "service_methods": ["list_contacts"],
  "repository_methods": ["get_all_contacts"],
  "authentication": "Bearer token (JWT)",
  "authorization": "User role required",
  "rate_limit": "100 requests/minute",
  "description": "List all contacts with filtering and pagination",
  "used_by_pages": [],
  "page_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### PUT /endpoint-docs/{endpoint_id}

Update endpoint documentation.

**Authentication:** Required (API key)

**Path Parameters:**
- `endpoint_id` (string, required): Unique endpoint identifier

**Request Body:** (all fields optional)
```json
{
  "description": "Updated endpoint description",
  "authentication": "Bearer token (JWT) required",
  "rate_limit": "200 requests/minute",
  "used_by_pages": [
    {
      "page_path": "/contacts",
      "page_title": "Contacts Page"
    }
  ],
  "page_count": 1
}
```

**Response:**
```json
{
  "_id": "123",
  "endpoint_id": "get_contacts_v4",
  "endpoint_path": "/api/v4/contacts",
  "method": "GET",
  "api_version": "v4",
  "description": "Updated endpoint description",
  "authentication": "Bearer token (JWT) required",
  "rate_limit": "200 requests/minute",
  "used_by_pages": [
    {
      "page_path": "/contacts",
      "page_title": "Contacts Page"
    }
  ],
  "page_count": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z"
}
```

### DELETE /endpoint-docs/{endpoint_id}

Delete endpoint documentation.

**Authentication:** Required (API key)

**Path Parameters:**
- `endpoint_id` (string, required): Unique endpoint identifier

**Response:**
```json
{
  "success": true,
  "message": "Endpoint documentation 'get_contacts_v4' deleted successfully"
}
```

### POST /endpoint-docs/sync

Sync endpoint documentation from analysis data.

**Authentication:** Required (API key)

**Request Body:**
```json
{
  "endpoints": [
    {
      "endpoint_path": "/api/v4/contacts",
      "method": "GET",
      "api_version": "v4",
      "router_file": "app/api/v4/endpoints/contacts.py",
      "description": "List contacts"
    },
    {
      "endpoint_path": "/api/v4/contacts/:id",
      "method": "GET",
      "api_version": "v4",
      "router_file": "app/api/v4/endpoints/contacts.py",
      "description": "Get contact by ID"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synced 2 endpoints",
  "data": {
    "synced_count": 2,
    "created_count": 2,
    "updated_count": 0
  }
}
```

## Relationships Endpoints

All endpoints require API key authentication.

### GET /docs/relationships/graph

Get full relationship graph (nodes and edges).

**Authentication:** Required (API key)

**Response:**
```json
{
  "nodes": [
    {
      "id": "page_about",
      "type": "page",
      "label": "About Page",
      "path": "/about"
    },
    {
      "id": "endpoint_get_contacts",
      "type": "endpoint",
      "label": "GET /api/v4/contacts",
      "path": "/api/v4/contacts"
    }
  ],
  "edges": [
    {
      "from": "page_about",
      "to": "endpoint_get_contacts",
      "type": "uses"
    }
  ]
}
```

### GET /docs/relationships/endpoint/{endpoint_path}

Get all pages using a specific endpoint.

**Authentication:** Required (API key)

**Path Parameters:**
- `endpoint_path` (string, required): Endpoint path (can include slashes, e.g., "/api/v4/contacts")

**Query Parameters:**
- `method` (string, optional): HTTP method filter (e.g., "GET")

**Example:**
```
GET /docs/relationships/endpoint/api/v4/contacts?method=GET
```

**Response:**
```json
{
  "pages": [
    {
      "page_path": "/contacts",
      "page_title": "Contacts Page"
    },
    {
      "page_path": "/about",
      "page_title": "About Page"
    }
  ]
}
```

### GET /docs/relationships/page/{page_path}

Get all endpoints used by a specific page.

**Authentication:** Required (API key)

**Path Parameters:**
- `page_path` (string, required): Page path (can include slashes, e.g., "/about")

**Example:**
```
GET /docs/relationships/page/about
```

**Response:**
```json
{
  "endpoints": [
    {
      "endpoint_path": "/api/v4/contacts",
      "method": "GET",
      "api_version": "v4"
    },
    {
      "endpoint_path": "/api/v4/companies",
      "method": "GET",
      "api_version": "v4"
    }
  ]
}
```

### GET /docs/relationships/statistics

Get relationship statistics.

**Authentication:** Required (API key)

**Response:**
```json
{
  "total_relationships": 150,
  "unique_pages": 45,
  "unique_endpoints": 78,
  "by_api_version": {
    "v1": 10,
    "v2": 20,
    "v3": 30,
    "v4": 90
  },
  "total_endpoints_documented": 100,
  "total_pages_documented": 50,
  "endpoints_with_pages": 60,
  "pages_with_endpoints": 40
}
```

### POST /docs/relationships/sync

Sync all relationships from analysis data.

**Authentication:** Required (API key)

**Request Body:**
```json
{
  "relationships": {
    "page_endpoint_links": [
      {
        "page_path": "/about",
        "endpoint_path": "/api/v4/contacts",
        "method": "GET",
        "api_version": "v4"
      },
      {
        "page_path": "/contact",
        "endpoint_path": "/api/v4/contacts",
        "method": "POST",
        "api_version": "v4"
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synced 2 relationships",
  "data": {
    "synced_relationships": 2,
    "created_count": 2,
    "updated_count": 0
  }
}
```

### GET /docs/relationships/validate

Validate relationships for broken links.

**Authentication:** Required (API key)

**Response:**
```json
{
  "total_relationships": 150,
  "issues": [
    {
      "type": "orphaned_relationship",
      "page_path": "/deleted_page",
      "endpoint_path": "/api/v4/contacts",
      "message": "Page not found"
    },
    {
      "type": "missing_endpoint",
      "page_path": "/about",
      "endpoint_path": "/api/v4/nonexistent",
      "message": "Endpoint not found"
    }
  ],
  "issue_count": 2,
  "valid": false
}
```

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid API key) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Rate Limiting

Currently no rate limiting is enforced. Consider implementing rate limiting for production use.

## Presigned URLs

Presigned URLs for S3 content are valid for 1 hour (3600 seconds) by default. This can be configured via `S3_PRESIGNED_URL_EXPIRATION` environment variable.

## Pagination

List endpoints support pagination via `limit` and `offset` query parameters:
- `limit`: Maximum number of results (1-1000, default: 100)
- `offset`: Number of results to skip (default: 0)

## Examples

### Create a Documentation Page

```bash
curl -X POST https://ostltf6zr0.execute-api.us-east-1.amazonaws.com/docs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "page_id": "about_page",
    "metadata": {
      "route": "/about",
      "purpose": "About page"
    },
    "content": "# About\n\nThis is the about page."
  }'
```

### List All Pages (Public)

```bash
curl https://ostltf6zr0.execute-api.us-east-1.amazonaws.com/docs
```

### Get Endpoint Documentation

```bash
curl -X GET https://ostltf6zr0.execute-api.us-east-1.amazonaws.com/endpoint-docs/get_contacts_v4 \
  -H "X-API-Key: your-api-key-here"
```

### Get Relationship Graph

```bash
curl -X GET https://ostltf6zr0.execute-api.us-east-1.amazonaws.com/docs/relationships/graph \
  -H "X-API-Key: your-api-key-here"
```

## Postman Collection

A complete Postman collection is available at:
`lambda/documentation.api/postman/Documentations API Service.postman_collection.json`

Import this collection into Postman to test all endpoints with pre-configured requests.

## Support

For issues or questions:
- Check CloudWatch logs for Lambda errors
- Review API Gateway logs
- See `lambda/documentation.api/README.md` for service documentation
