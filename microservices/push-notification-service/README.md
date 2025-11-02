# Push Notification Service

## Overview

This is a standalone FastAPI microservice that handles web push notifications, extracted from the main Django portfolio application as part of the microservices architecture migration.

## Architecture Design

### Service Responsibilities
- Web push subscription management
- Push notification delivery
- Notification logging and analytics
- VAPID key management
- Rate limiting and security

### API Contract

#### Base URL
- Development: `http://localhost:8001`
- Production: `https://push-api.yourdomain.com`

#### Authentication
- JWT tokens from main Django application
- API key authentication for service-to-service communication

#### Endpoints

##### Subscription Management
```
POST /subscriptions/
- Create new push subscription
- Body: subscription data (endpoint, keys)
- Response: subscription ID and confirmation

GET /subscriptions/{id}/
- Get subscription details
- Requires authentication

PUT /subscriptions/{id}/
- Update subscription (topics, enabled status)
- Body: updated subscription data

DELETE /subscriptions/{id}/
- Remove subscription
- Soft delete for analytics
```

##### Notification Sending
```
POST /notifications/send/
- Send push notification
- Body: notification payload and target criteria
- Response: delivery results and statistics

POST /notifications/broadcast/
- Send notification to all active subscribers
- Body: notification payload
- Response: delivery results

GET /notifications/history/
- Get notification history
- Query params: page, limit, type, status
```

##### Analytics
```
GET /analytics/subscriptions/
- Subscription statistics
- Query params: date_from, date_to

GET /analytics/deliveries/
- Delivery statistics and success rates
- Query params: date_from, date_to, type
```

##### Health & Monitoring
```
GET /health/
- Service health check
- Returns: status, version, dependencies

GET /metrics/
- Prometheus metrics endpoint
- Returns: service metrics in Prometheus format
```

## Data Models

### Subscription
```json
{
    "id": "uuid",
    "endpoint": "string",
    "p256dh": "string",
    "auth": "string",
    "topics": ["string"],
    "enabled": "boolean",
    "user_id": "string (optional)",
    "created_at": "datetime",
    "updated_at": "datetime",
    "last_used": "datetime"
}
```

### Notification
```json
{
    "id": "uuid",
    "title": "string",
    "body": "string",
    "icon": "string (optional)",
    "image": "string (optional)",
    "badge": "string (optional)",
    "url": "string (optional)",
    "tag": "string (optional)",
    "type": "string",
    "actions": [
        {
            "action": "string",
            "title": "string",
            "icon": "string (optional)"
        }
    ],
    "created_at": "datetime",
    "scheduled_at": "datetime (optional)"
}
```

### Delivery Log
```json
{
    "id": "uuid",
    "notification_id": "uuid",
    "subscription_id": "uuid",
    "status": "pending|sent|delivered|failed|expired",
    "response_code": "integer",
    "error_message": "string (optional)",
    "sent_at": "datetime",
    "delivered_at": "datetime (optional)"
}
```

## Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations

### Database
- **PostgreSQL**: Primary database (shared with Django app)
- **Redis**: Caching and rate limiting

### Web Push
- **py-webpush**: Python web push protocol implementation
- **cryptography**: VAPID key generation and management

### Monitoring & Observability
- **Prometheus**: Metrics collection
- **Sentry**: Error tracking and performance monitoring
- **Structlog**: Structured logging

### Deployment
- **Docker**: Containerization
- **Gunicorn**: WSGI server for production
- **nginx**: Reverse proxy and load balancing

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db_name
REDIS_URL=redis://localhost:6379/0

# VAPID Keys
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_SUBJECT=mailto:admin@yourdomain.com

# Security
JWT_SECRET_KEY=your_jwt_secret
API_KEY=your_api_key

# External Services
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_METRICS_ENABLED=true

# Rate Limiting
RATE_LIMIT_SUBSCRIPTION=100/hour
RATE_LIMIT_NOTIFICATION=50/hour
RATE_LIMIT_ANALYTICS=200/hour
```

## Migration Strategy

### Phase 1: API Contract Definition ✅
- Define service boundaries and responsibilities
- Design API endpoints and data models
- Document authentication and security requirements

### Phase 2: Service Implementation
- Create FastAPI application structure
- Implement core endpoints
- Add database models and migrations
- Set up authentication and rate limiting

### Phase 3: Data Migration
- Extract notification-related data from Django app
- Set up database schema in new service
- Implement data synchronization

### Phase 4: Integration & Testing
- Update Django app to use new service
- Implement fallback mechanisms
- Add comprehensive testing
- Load testing and performance optimization

### Phase 5: Deployment & Monitoring
- Set up production infrastructure
- Configure monitoring and alerting
- Gradual traffic migration
- Performance monitoring and optimization

## Integration with Django Application

### Service Client
```python
# In Django app
from services.push_notification_client import PushNotificationClient

client = PushNotificationClient(
    base_url=settings.PUSH_SERVICE_URL,
    api_key=settings.PUSH_SERVICE_API_KEY
)

# Send notification
result = await client.send_notification(
    title="New Blog Post",
    body="Check out the latest article",
    topics=["blog"],
    url="/blog/latest-post"
)
```

### Fallback Strategy
- Keep existing Django implementation as fallback
- Graceful degradation when microservice is unavailable
- Circuit breaker pattern for resilience

## Development Setup

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd push-notification-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8001
```

### Docker Development
```bash
# Build and run with docker-compose
docker-compose -f docker-compose.dev.yml up --build
```

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Load Testing
```bash
# Using locust
locust -f tests/load/test_notifications.py --host http://localhost:8001
```

## Security Considerations

### Authentication
- JWT token validation with Django app
- API key authentication for service communication
- Rate limiting per client/IP

### Data Protection
- HTTPS only in production
- Secure headers (HSTS, CSP)
- Input validation and sanitization
- SQL injection protection via ORM

### Push Security
- VAPID key rotation capability
- Subscription validation
- TTL enforcement for notifications

## Monitoring & Alerting

### Key Metrics
- Notification delivery rate
- API response times
- Error rates by endpoint
- Active subscription count
- Queue length for pending notifications

### Alerts
- High error rates (>5%)
- Slow response times (>500ms)
- Service unavailability
- Database connection issues
- High queue backlog

## Future Enhancements

### Planned Features
- Scheduled notifications
- A/B testing for notification content
- Rich notification templates
- Push notification analytics dashboard
- Multi-tenancy support

### Scalability Improvements
- Message queue integration (RabbitMQ/Kafka)
- Horizontal scaling with load balancing
- Database read replicas
- CDN integration for notification assets
