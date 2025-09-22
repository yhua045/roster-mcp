# Roster API Documentation

## Overview

The Roster API provides endpoints for managing church service rosters, including retrieving historical roster data, creating new events, and updating member assignments.

## Base URL

```
https://api.example.com
```

## Authentication

API requests may require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### GET /api/events

Retrieve events within a specified date range and optional category filter.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `category` | string | No | - | Service category filter (case-insensitive). See allowed values below. |
| `from` | string (ISO date) | No | today | Start date for filtering (inclusive). Format: YYYY-MM-DD |
| `to` | string (ISO date) | No | today + 7 days | End date for filtering (inclusive). Format: YYYY-MM-DD |

#### Allowed Category Values

The `category` parameter accepts the following case-insensitive values:
- `chinese` - Chinese language service
- `english` - English language service
- `sundayschool` - Sunday school service

#### Request Examples

##### Get all events for the next 7 days (default behavior)
```http
GET /api/events
```

##### Get Chinese service events for January 2024
```http
GET /api/events?category=chinese&from=2024-01-01&to=2024-01-31
```

##### Get all events for a specific date range
```http
GET /api/events?from=2024-01-14&to=2024-01-21
```

##### Get English service events (case-insensitive)
```http
GET /api/events?category=English&from=2024-02-01&to=2024-02-29
```

#### Response

##### Success Response (200 OK)

Returns an array of event objects:

```json
[
  {
    "id": 1,
    "date": "2024-01-14",
    "category": "chinese",
    "serviceInfo": {
      "id": 101,
      "footnote": "Special service",
      "skipService": false,
      "skipReason": null
    },
    "members": [
      {
        "id": 501,
        "role": "證道",
        "name": "Pastor Chen",
        "personId": 42,
        "confirmed": true,
        "notes": null
      },
      {
        "id": 502,
        "role": "司會",
        "name": "John Smith",
        "personId": 43,
        "confirmed": true,
        "notes": null
      }
    ]
  },
  {
    "id": 2,
    "date": "2024-01-14",
    "category": "english",
    "serviceInfo": {
      "id": 102,
      "footnote": null,
      "skipService": false,
      "skipReason": null
    },
    "members": [
      {
        "id": 503,
        "role": "Preacher",
        "name": "Pastor Johnson",
        "personId": 44,
        "confirmed": true,
        "notes": null
      }
    ]
  }
]
```

##### Empty Result (200 OK)

When no events match the criteria:

```json
[]
```

#### Error Responses

##### Invalid Category (400 Bad Request)

When an invalid category value is provided:

```json
{
  "message": "Invalid category: 'invalidvalue'. Must be one of ['chinese', 'english', 'sundayschool']",
  "errors": {
    "category": "Invalid value"
  }
}
```

##### Invalid Date Format (400 Bad Request)

When date parameters are malformed:

```json
{
  "message": "Invalid date format",
  "errors": {
    "from": "Invalid date format: '2024/01/14'. Expected YYYY-MM-DD"
  }
}
```

##### Invalid Date Range (400 Bad Request)

When `from` date is after `to` date:

```json
{
  "message": "Invalid date range",
  "errors": {
    "date_range": "Invalid date range: 'from' date (2024-02-01) must be before or equal to 'to' date (2024-01-01)"
  }
}
```

##### Server Error (500 Internal Server Error)

```json
{
  "error": "Internal server error"
}
```

### GET /api/events/{id}

Retrieve a specific event by ID.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Event identifier (in URL path) |

#### Request Example

```http
GET /api/events/123
```

#### Response

Returns a single event object (same structure as in GET /api/events response).

### POST /api/events

Create a new event.

#### Request Body

```json
{
  "date": "2024-01-21",
  "category": "chinese",
  "serviceInfo": {
    "footnote": "Special service",
    "skipService": false,
    "skipReason": null
  },
  "members": [
    {
      "role": "證道",
      "name": "Pastor Chen",
      "personId": 42
    }
  ]
}
```

#### Response

Returns the created event object with generated IDs.

### PUT /api/events/{id}

Update an existing event or add members to an event.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Event identifier (in URL path) |

#### Request Body

Same structure as POST /api/events.

#### Response

Returns the updated event object.

## Error Handling

All error responses follow a consistent format:

```json
{
  "message": "Human-readable error message",
  "errors": {
    "field_name": "Specific error detail"
  }
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Validation error or invalid parameters
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

API requests may be subject to rate limiting. Check response headers for rate limit information:

- `X-RateLimit-Limit` - Maximum requests per hour
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Unix timestamp when the rate limit resets

## Versioning

The API version is included in the URL path. The current version is v1 (implicit in the base URL).

## Security Considerations

- Always use HTTPS for API requests
- Never expose API keys in client-side code
- Implement proper error handling to avoid exposing sensitive information
- Validate and sanitize all input data before sending to the API