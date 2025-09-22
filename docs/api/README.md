# 🔌 API & Integrations

API documentation, third-party integrations, and external service configurations for the Portfolio Project.

## 📋 Available Guides

### [Gemini AI Integration](./GEMINI.md)
Google's Gemini AI service integration guide.
- API key configuration
- Service initialization
- Usage examples
- Error handling
- Rate limiting considerations

## 🌐 API Overview

### REST API Endpoints

#### Authentication
```
POST /api/auth/login/          # User login
POST /api/auth/logout/         # User logout
POST /api/auth/refresh/        # Refresh token
```

#### Portfolio
```
GET  /api/portfolio/projects/  # List projects
GET  /api/portfolio/skills/    # List skills
GET  /api/portfolio/experience/ # Get experience
```

#### Blog
```
GET  /api/blog/posts/          # List blog posts
GET  /api/blog/posts/{id}/     # Get specific post
GET  /api/blog/categories/     # List categories
GET  /api/blog/tags/           # List tags
```

#### Tools
```
GET  /api/tools/               # List tools
GET  /api/tools/{id}/          # Get specific tool
POST /api/tools/search/        # Search tools
```

#### Contact
```
POST /api/contact/             # Submit contact form
GET  /api/contact/messages/    # List messages (admin)
```

### WebSocket Endpoints
```
ws://localhost:8000/ws/chat/   # Real-time chat
ws://localhost:8000/ws/notifications/ # Push notifications
```

## 🔑 Authentication

### API Key Authentication
```python
# In your requests
headers = {
    'Authorization': 'Api-Key your-api-key-here',
    'Content-Type': 'application/json'
}
```

### JWT Token Authentication
```python
# Login to get token
response = requests.post('/api/auth/login/', {
    'username': 'user',
    'password': 'pass'
})
token = response.json()['access']

# Use token in requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
```

## 🔧 Third-Party Integrations

### Google Services
- **Gemini AI**: Advanced AI capabilities
- **Analytics**: Website traffic analysis
- **Search Console**: SEO monitoring
- **Maps API**: Location services

### Social Media
- **Twitter API**: Social media integration
- **LinkedIn API**: Professional networking
- **GitHub API**: Repository information

### Monitoring & Analytics
- **Sentry**: Error tracking and performance
- **Mixpanel**: User behavior analytics
- **Hotjar**: User experience insights

## 📊 API Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Sample Post",
    "content": "Post content here..."
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": ["This field is required"]
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid-here"
  }
}
```

### Pagination
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "count": 100,
    "next": "http://api.example.com/posts/?page=2",
    "previous": null,
    "page": 1,
    "total_pages": 10
  }
}
```

## 🚦 Rate Limiting

### Default Limits
- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Premium users**: 10000 requests/hour

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🔒 Security

### CORS Configuration
```python
# Allowed origins for API access
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]
```

### API Security Headers
- **Content-Type validation**
- **CSRF protection**
- **Input sanitization**
- **SQL injection prevention**

## 📝 Usage Examples

### Python Client
```python
import requests

# Get blog posts
response = requests.get('http://localhost:8000/api/blog/posts/')
posts = response.json()['data']

# Create new post (authenticated)
headers = {'Authorization': 'Bearer your-token'}
data = {
    'title': 'New Post',
    'content': 'Post content...'
}
response = requests.post(
    'http://localhost:8000/api/blog/posts/',
    json=data,
    headers=headers
)
```

### JavaScript Client
```javascript
// Fetch posts
const response = await fetch('/api/blog/posts/');
const data = await response.json();
const posts = data.data;

// Create post with authentication
const token = localStorage.getItem('token');
const response = await fetch('/api/blog/posts/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'New Post',
    content: 'Post content...'
  })
});
```

---
[← Back to Documentation](../README.md)