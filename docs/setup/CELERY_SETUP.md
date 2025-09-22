# Celery Background Task Processing Setup

## Overview

This document describes the comprehensive Celery setup for asynchronous task processing, scheduling, and monitoring.

## Features Implemented

✅ **Redis Broker Configuration**
- Redis as message broker for task queue
- Fallback to SQLite-based task storage
- Connection pooling and retry mechanisms

✅ **Celery Beat Scheduler**
- Database-backed periodic task scheduling
- Pre-configured scheduled tasks for maintenance
- Django admin integration for task management

✅ **Flower Monitoring**
- Web-based task monitoring dashboard
- Real-time task execution tracking
- Worker performance metrics

✅ **Advanced Task Retry Logic**
- Exponential backoff retry strategy
- Per-task retry configuration
- Comprehensive error handling

## Configuration Details

### Settings (portfolio_site/settings/base.py)
```python
# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

# Task Configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Beat Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task Routing
CELERY_TASK_ROUTES = {
    'apps.main.tasks.send_notification': {'queue': 'high_priority'},
    'apps.main.tasks.process_user_action': {'queue': 'high_priority'},
    'apps.main.tasks.update_analytics': {'queue': 'default'},
    'apps.main.tasks.cleanup_temp_files': {'queue': 'default'},
    'apps.main.tasks.generate_reports': {'queue': 'low_priority'},
    'apps.main.tasks.backup_data': {'queue': 'low_priority'},
}

# Worker Configuration
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task Limits and Retries
CELERY_TASK_SOFT_TIME_LIMIT = 60   # 1 minute
CELERY_TASK_TIME_LIMIT = 120       # 2 minutes
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60

# Result Storage
CELERY_RESULT_EXPIRES = 3600  # 1 hour
```

### Available Tasks

1. **send_notification**
   - Queue: high_priority
   - Retries: 3 attempts with 60s delay
   - Purpose: Send notifications to users via multiple channels

2. **process_user_action**
   - Queue: high_priority
   - Retries: 2 attempts with 30s delay
   - Purpose: Process user interactions asynchronously

3. **update_analytics**
   - Queue: default
   - Schedule: Every 5 minutes
   - Purpose: Update analytics data and metrics

4. **cleanup_temp_files**
   - Queue: default
   - Schedule: Every hour
   - Purpose: Clean up temporary files and cache entries

5. **health_check**
   - Queue: default
   - Schedule: Every minute
   - Purpose: System health monitoring

6. **generate_reports**
   - Queue: low_priority
   - Purpose: Generate system and performance reports

7. **backup_data**
   - Queue: low_priority
   - Purpose: Data backup operations

## Usage Instructions

### Starting Services

#### Option 1: Individual Commands
```bash
# Start Redis server (required)
redis-server

# Start Celery worker
celery -A portfolio_site worker --loglevel=info

# Start Celery Beat scheduler
celery -A portfolio_site beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler

# Start Flower monitoring
celery -A portfolio_site flower
```

#### Option 2: Service Manager Script
```bash
python start_celery_services.py
```

This starts all services with appropriate configurations:
- Multiple workers for different priority queues
- Beat scheduler with database persistence
- Flower monitoring on http://localhost:5555

### Testing

Run comprehensive tests:
```bash
python test_celery_setup.py
```

Test specific task types:
```bash
python manage.py test_celery --task=notification
python manage.py test_celery --task=analytics
python manage.py test_celery --task=all
```

### Management Commands

#### Start Flower Monitoring
```bash
python manage.py start_flower --port=5555
```

#### Test Task Execution
```bash
python manage.py test_celery
```

### Monitoring and Management

#### Flower Dashboard
- URL: http://localhost:5555
- Features:
  - Real-time task monitoring
  - Worker status and statistics
  - Task history and results
  - Queue management

#### Django Admin
- Periodic tasks management at `/admin/django_celery_beat/`
- Task results at `/admin/django_celery_results/`

#### CLI Commands
```bash
# Check worker status
celery -A portfolio_site status

# Inspect active tasks
celery -A portfolio_site inspect active

# Inspect scheduled tasks
celery -A portfolio_site inspect scheduled

# Cancel task
celery -A portfolio_site revoke <task_id>

# Purge all tasks
celery -A portfolio_site purge
```

## Queue Configuration

### High Priority Queue
- Workers: 2
- Tasks: Notifications, user actions
- Processing: Immediate priority

### Default Queue
- Workers: 4
- Tasks: Analytics, cleanup, health checks
- Processing: Normal priority

### Low Priority Queue
- Workers: 2
- Tasks: Reports, backups
- Processing: Background processing

## Error Handling and Retry Logic

### Retry Strategy
1. **Exponential Backoff**: Delays increase with each retry attempt
2. **Max Retries**: Configurable per task (2-3 attempts)
3. **Jitter**: Random delay variation to prevent thundering herd

### Error Monitoring
- All task failures logged with structured format
- Error tracking through Django logging system
- Optional Sentry integration for production monitoring

### Failure Recovery
- Failed tasks automatically retry with increasing delays
- Persistent task state in database
- Dead letter queue for permanently failed tasks

## Production Considerations

### Redis Configuration
- Use Redis Cluster for high availability
- Configure appropriate memory limits
- Set up Redis persistence (AOF + RDB)

### Worker Deployment
- Run multiple worker processes across servers
- Use supervisor or systemd for process management
- Configure proper logging and monitoring

### Performance Tuning
- Adjust concurrency based on server resources
- Optimize task serialization for large payloads
- Use task prioritization for critical operations

### Security
- Use Redis AUTH for broker authentication
- Encrypt sensitive task payloads
- Implement task-level access controls

## Verification Checklist

- [x] Redis connection established
- [x] Celery workers start successfully
- [x] Beat scheduler creates periodic tasks
- [x] Flower monitoring accessible
- [x] Tasks execute asynchronously
- [x] Task retry logic functions correctly
- [x] Queue routing works as configured
- [x] Error handling and logging operational
- [x] Management commands functional
- [x] Database migrations applied

## Next Steps

1. **Start Redis Server**: Ensure Redis is running for production use
2. **Deploy Workers**: Set up worker processes on production servers
3. **Configure Monitoring**: Set up alerts for task failures and worker health
4. **Performance Testing**: Load test with expected task volumes
5. **Documentation**: Update operational runbooks

## Troubleshooting

### Common Issues

**Redis Connection Error**
```
Solution: Ensure Redis server is running and accessible at configured URL
```

**Worker Not Processing Tasks**
```
Solution: Check worker logs, verify queue names match task routing
```

**Beat Not Creating Scheduled Tasks**
```
Solution: Verify django_celery_beat migrations applied, check database connectivity
```

**Flower Not Accessible**
```
Solution: Check port configuration, ensure no firewall blocking access
```

For detailed troubleshooting, check logs in:
- Worker logs: Console output or configured log files
- Django logs: `logs/django.log`
- Performance logs: `logs/performance.log`
- Error logs: `logs/errors.log`