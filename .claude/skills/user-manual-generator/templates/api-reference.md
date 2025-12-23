# Template: API Reference

Use this template for creating user-focused API reference documentation.

---

```markdown
# API Reference

## Authentication

All API requests require authentication using an API key.

**Getting your API key**: [How to obtain]

**Using your API key**:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.example.com/endpoint
```

## Rate Limits

- **Free tier**: 100 requests/hour
- **Pro tier**: 1000 requests/hour

When you exceed the limit, you'll receive a `429 Too Many Requests` response.

## Endpoints

### Create a Resource

`POST /api/resources`

Creates a new resource.

**Request Body**:

```json
{
  "name": "Resource Name",
  "type": "resource-type",
  "options": {
    "enabled": true
  }
}
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | The resource name (max 255 chars) |
| `type` | string | Yes | One of: `type1`, `type2` |
| `options` | object | No | Configuration options |

**Response** (201 Created):

```json
{
  "id": "res_abc123",
  "name": "Resource Name",
  "type": "resource-type",
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Example**:

```bash
curl -X POST https://api.example.com/api/resources \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Resource",
    "type": "type1"
  }'
```

**Errors**:

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 400 | Invalid request body | Check required fields |
| 401 | Missing/invalid API key | Verify your API key |
| 409 | Resource already exists | Use a different name |

### Get a Resource

`GET /api/resources/:id`

Retrieves a specific resource by ID.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | The resource ID |

**Response** (200 OK):

```json
{
  "id": "res_abc123",
  "name": "Resource Name",
  "type": "resource-type",
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Errors**:

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 404 | Resource not found | Verify the resource ID |

### List Resources

`GET /api/resources`

Lists all resources with pagination.

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | number | 1 | Page number |
| `limit` | number | 20 | Items per page (max 100) |
| `sort` | string | `created_at` | Sort field |

**Response** (200 OK):

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```
```

---

## Template Notes

- Start with authentication section
- Include rate limits prominently
- Document every endpoint with method, path, parameters
- Show request body and response for each
- Include curl examples for each endpoint
- List all possible error codes with solutions
