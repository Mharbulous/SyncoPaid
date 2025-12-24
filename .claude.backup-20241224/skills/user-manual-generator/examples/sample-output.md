# Sample Output: Express.js API Documentation

This example shows the documentation generated for a sample Express.js REST API project.

## Input Project Structure

```
my-api-project/
├── src/
│   ├── server.js
│   ├── routes/
│   │   ├── auth.js
│   │   ├── users.js
│   │   └── posts.js
│   ├── middleware/
│   │   ├── auth.middleware.js
│   │   └── rateLimiter.js
│   ├── models/
│   │   ├── User.js
│   │   └── Post.js
│   └── config/
│       └── database.js
├── .env.example
├── package.json
└── README.md
```

## Skill Invocation

**User prompt**:
```
Use the user-manual-generator skill to create API documentation for developer integration
```

## Skill Questions & Answers

```
Q: What type of application is this?
A: REST API

Q: Who will use this documentation?
A: API consumers (developers integrating your service)

Q: Which documentation framework do you prefer?
A: Docusaurus

Q: Where will you host the documentation?
A: GitHub Pages

Q: How comprehensive should the documentation be?
A: Standard (getting started + common tasks + reference)

Q: Should I include additional sections?
A: Yes - Troubleshooting guide, FAQ, Changelog template
```

## Generated Documentation Structure

```
docs/
├── docs/
│   ├── index.md                          # API overview
│   ├── getting-started/
│   │   ├── installation.md               # SDK installation
│   │   ├── authentication.md             # Getting API keys
│   │   └── first-request.md              # Hello world API call
│   ├── guides/
│   │   ├── authentication-flow.md        # OAuth & JWT explained
│   │   ├── rate-limiting.md              # Handling rate limits
│   │   ├── pagination.md                 # Paginating large results
│   │   ├── error-handling.md             # Handling API errors
│   │   └── webhooks.md                   # Setting up webhooks
│   ├── reference/
│   │   ├── authentication-endpoints.md   # Auth endpoints
│   │   ├── users-endpoints.md            # User CRUD endpoints
│   │   ├── posts-endpoints.md            # Post endpoints
│   │   ├── error-codes.md                # All error codes
│   │   └── rate-limits.md                # Rate limit details
│   ├── explanation/
│   │   ├── architecture.md               # API architecture
│   │   └── security.md                   # Security model
│   └── troubleshooting/
│       ├── common-errors.md              # Error solutions
│       └── faq.md                        # FAQ
├── docusaurus.config.js
├── sidebars.js
├── package.json
└── DEPLOYMENT.md
```

## Sample Generated Content

### docs/index.md (Excerpt)

```markdown
# My API Documentation

Welcome to the My API documentation. This API allows you to manage users and posts with a RESTful interface.

## Quick Links

- [Get Started in 5 Minutes](getting-started/first-request.md)
- [Authentication Guide](getting-started/authentication.md)
- [Complete API Reference](reference/users-endpoints.md)
- [Error Codes](reference/error-codes.md)

## Features

- **RESTful Design**: Clean, predictable endpoints
- **JWT Authentication**: Secure token-based auth
- **Rate Limiting**: Fair usage with 100 requests/hour (free tier)
- **Pagination**: Efficient handling of large datasets
- **Webhooks**: Real-time event notifications

## Base URL

```
https://api.example.com/v1
```

## Authentication

All API requests require authentication using a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.example.com/v1/users
```

[Get your API key](getting-started/authentication.md)

## Quick Example

```javascript
const axios = require('axios');

const response = await axios.get('https://api.example.com/v1/users', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
});

console.log(response.data);
```

## Rate Limits

- **Free tier**: 100 requests/hour
- **Pro tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

See [Rate Limiting Guide](guides/rate-limiting.md) for details.

## Need Help?

- [FAQ](troubleshooting/faq.md)
- [Common Errors](troubleshooting/common-errors.md)
- [GitHub Issues](https://github.com/username/repo/issues)
```

### docs/reference/users-endpoints.md (Excerpt)

```markdown
# Users API Reference

Endpoints for managing users.

## List Users

`GET /api/v1/users`

Retrieve a paginated list of users.

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 20 | Results per page (max 100) |
| `sort` | string | No | `created_at` | Sort field (`created_at`, `name`, `email`) |
| `order` | string | No | `desc` | Sort order (`asc`, `desc`) |

### Example Request

```bash
curl -X GET "https://api.example.com/v1/users?page=1&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Example Response (200 OK)

```json
{
  "data": [
    {
      "id": "usr_abc123",
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "usr_def456",
      "email": "jane@example.com",
      "name": "Jane Smith",
      "created_at": "2025-01-14T08:20:00Z",
      "updated_at": "2025-01-14T08:20:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total": 50,
    "total_pages": 5
  }
}
```

### Error Responses

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 401 | Missing or invalid API key | Check your Authorization header |
| 429 | Rate limit exceeded | Wait or upgrade your plan |
| 500 | Server error | Retry with exponential backoff |

---

## Create User

`POST /api/v1/users`

Create a new user.

### Request Body

```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "securepassword123"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address (unique) |
| `name` | string | Yes | User's full name (max 255 chars) |
| `password` | string | Yes | Min 8 chars, must include letter & number |

### Example Request

```bash
curl -X POST "https://api.example.com/v1/users" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "name": "New User",
    "password": "securepass123"
  }'
```

### Example Response (201 Created)

```json
{
  "id": "usr_xyz789",
  "email": "newuser@example.com",
  "name": "New User",
  "created_at": "2025-01-15T14:22:00Z",
  "updated_at": "2025-01-15T14:22:00Z"
}
```

### Error Responses

| Status Code | Error Code | Message | Solution |
|-------------|------------|---------|----------|
| 400 | `invalid_email` | Invalid email format | Use valid email |
| 400 | `weak_password` | Password too weak | Min 8 chars with letter & number |
| 409 | `email_exists` | Email already registered | Use different email |

---

[More endpoints...]
```

### docs/guides/rate-limiting.md (Excerpt)

```markdown
# Handling Rate Limits

Learn how to work within API rate limits and handle rate limit errors gracefully.

## Rate Limit Tiers

| Tier | Requests/Hour | Requests/Day | Cost |
|------|---------------|--------------|------|
| Free | 100 | 1,000 | $0 |
| Pro | 1,000 | 10,000 | $29/mo |
| Enterprise | Custom | Custom | Contact sales |

## Checking Your Rate Limit

Every API response includes rate limit headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642251600
```

- **X-RateLimit-Limit**: Your total requests allowed per hour
- **X-RateLimit-Remaining**: Requests remaining in current window
- **X-RateLimit-Reset**: Unix timestamp when limit resets

## Handling 429 Errors

When you exceed the rate limit, you'll receive:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Retry after 1800 seconds.",
    "retry_after": 1800
  }
}
```

**Status Code**: `429 Too Many Requests`

### Recommended Retry Logic

```javascript
async function apiRequest(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || 60;
        console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
        await sleep(retryAfter * 1000);
        continue; // Retry
      }

      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

## Best Practices

1. **Monitor rate limit headers**: Check `X-RateLimit-Remaining` before making requests
2. **Implement exponential backoff**: Don't immediately retry on 429
3. **Cache responses**: Reduce unnecessary API calls
4. **Batch requests**: Combine multiple operations when possible
5. **Upgrade if needed**: Consider Pro tier for higher limits

## Optimizing Request Usage

### Use Pagination Wisely

Instead of requesting all records:
```javascript
// ❌ Bad: Request all users (could be thousands)
const allUsers = await getUsers({ limit: 10000 });

// ✅ Good: Request only what you need
const recentUsers = await getUsers({ limit: 20, sort: 'created_at' });
```

### Cache Responses

```javascript
const cache = new Map();

async function getCachedUser(userId) {
  if (cache.has(userId)) {
    return cache.get(userId);
  }

  const user = await apiRequest(`/users/${userId}`);
  cache.set(userId, user);

  // Expire after 5 minutes
  setTimeout(() => cache.delete(userId), 5 * 60 * 1000);

  return user;
}
```

### Use Webhooks for Real-Time Updates

Instead of polling for changes, use webhooks:

```javascript
// ❌ Bad: Poll every 10 seconds (360 requests/hour)
setInterval(async () => {
  const posts = await getPosts();
  // Check for changes
}, 10000);

// ✅ Good: Receive webhook notifications (0 requests, instant updates)
// Configure webhook endpoint: https://yourapp.com/webhooks/posts
```

See [Webhooks Guide](webhooks.md) for setup.

## Monitoring Your Usage

Track your API usage to avoid surprises:

```javascript
let requestCount = 0;
let resetTime = null;

function trackRateLimit(response) {
  requestCount++;
  const remaining = response.headers.get('X-RateLimit-Remaining');
  resetTime = new Date(response.headers.get('X-RateLimit-Reset') * 1000);

  console.log(`Requests made: ${requestCount}`);
  console.log(`Remaining: ${remaining}`);
  console.log(`Resets at: ${resetTime}`);

  if (remaining < 10) {
    console.warn('⚠️ Approaching rate limit!');
  }
}
```

## Need Higher Limits?

[Upgrade to Pro](https://example.com/pricing) for 10x higher limits or [contact sales](mailto:sales@example.com) for custom Enterprise limits.
```

## Generated Configuration Files

### docusaurus.config.js (Excerpt)

```javascript
module.exports = {
  title: 'My API Documentation',
  tagline: 'Developer guide for My API',
  url: 'https://username.github.io',
  baseUrl: '/my-api/',
  organizationName: 'username',
  projectName: 'my-api',

  themeConfig: {
    navbar: {
      title: 'My API',
      items: [
        {
          type: 'doc',
          docId: 'getting-started/authentication',
          position: 'left',
          label: 'Getting Started',
        },
        {
          type: 'doc',
          docId: 'guides/authentication-flow',
          position: 'left',
          label: 'Guides',
        },
        {
          type: 'doc',
          docId: 'reference/users-endpoints',
          position: 'left',
          label: 'API Reference',
        },
        {
          href: 'https://github.com/username/my-api',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    // ... more configuration
  },
};
```

## Generation Report Summary

```
✅ Documentation generation complete!

📊 Summary:
- Generated 18 documentation pages (~15,000 words)
- Set up Docusaurus static site
- Ready for deployment to GitHub Pages

📝 Files created:
- Getting Started: 3 guides
- How-To Guides: 5 guides
- API Reference: 4 endpoint docs
- Troubleshooting: 2 guides
- Configuration: Complete Docusaurus setup

⚠️ Manual review needed:
- Verify all endpoint examples work
- Add authentication flow diagram (placeholder added)
- Review error messages for accuracy
- Add webhook setup screenshots (placeholders added)

🚀 Next steps:
1. cd docs && npm install && npm start
2. Review generated content
3. Add diagrams and screenshots
4. Deploy: GIT_USER=username npm run deploy

Estimated time saved: ~12 hours of manual documentation work
```

## Time Comparison

| Task | Manual | With Skill | Savings |
|------|--------|------------|---------|
| Structure planning | 1 hour | 0 min | 100% |
| Writing getting started | 2 hours | 10 min | 92% |
| API reference docs | 6 hours | 15 min | 96% |
| How-to guides | 3 hours | 20 min | 89% |
| SSG setup | 1 hour | 5 min | 92% |
| **Total** | **13 hours** | **50 min** | **94%** |

**Note**: Manual refinement (screenshots, verification) estimated at 2-3 additional hours, still resulting in ~70% time savings overall.
