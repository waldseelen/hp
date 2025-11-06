# CDN Configuration Guide

## Overview

This guide explains how to configure and use a Content Delivery Network (CDN) for your Django application. We recommend **Cloudflare** as the CDN provider due to its free tier, ease of use, and excellent performance.

## Why Use a CDN?

- **Faster Load Times**: Static files served from locations closer to users
- **Reduced Bandwidth**: Offload static file serving from your origin server
- **Better Caching**: Intelligent caching at edge locations worldwide
- **DDoS Protection**: Built-in security and DDoS mitigation
- **SSL/TLS**: Free SSL certificates and HTTPS support

## Cloudflare Setup

### 1. Create Cloudflare Account

1. Go to [cloudflare.com](https://www.cloudflare.com)
2. Sign up for a free account
3. Add your domain

### 2. Update DNS Settings

1. In Cloudflare dashboard, go to DNS settings
2. Update your domain's nameservers to Cloudflare's nameservers (provided in dashboard)
3. Wait for DNS propagation (can take 24-48 hours)

### 3. Configure Cache Rules

#### Cache Everything Rule

```
Rule Name: Cache Static Files
URL Pattern: *example.com/static/*
Cache Level: Cache Everything
Edge Cache TTL: 1 year
Browser Cache TTL: 1 year
```

#### Media Files Rule

```
Rule Name: Cache Media Files
URL Pattern: *example.com/media/*
Cache Level: Cache Everything
Edge Cache TTL: 1 month
Browser Cache TTL: 1 month
```

### 4. Enable Performance Features

In Cloudflare dashboard, enable:
- [x] Auto Minify (HTML, CSS, JS)
- [x] Brotli Compression
- [x] Rocket Loader (optional - test first)
- [x] HTTP/2 and HTTP/3
- [x] Early Hints
- [x] WebP image conversion

### 5. Configure Django Settings

Add to your `.env` file:

```bash
CDN_ENABLED=True
CDN_DOMAIN=cdn.yourdomain.com  # Or use your main domain
```

Update `project/settings/production.py`:

```python
# CDN Configuration
CDN_ENABLED = config("CDN_ENABLED", default=False, cast=bool)
CDN_DOMAIN = config("CDN_DOMAIN", default="")

# If CDN is enabled, use CDN domain for static files
if CDN_ENABLED and CDN_DOMAIN:
    STATIC_URL = f"https://{CDN_DOMAIN}/static/"
    MEDIA_URL = f"https://{CDN_DOMAIN}/media/"
```

### 6. Update Middleware

Add CDN middleware to `MIDDLEWARE` in `settings/base.py`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'apps.core.middleware.cdn_middleware.CDNMiddleware',
    'apps.core.middleware.cdn_middleware.CompressionMiddleware',
    # ... rest of middleware ...
]
```

## Alternative CDN Providers

### Amazon CloudFront

**Pros:**
- Deep AWS integration
- Fine-grained control
- Global edge network

**Cons:**
- More complex setup
- Pay-as-you-go pricing
- Requires S3 bucket

**Setup Steps:**
1. Create S3 bucket for static files
2. Create CloudFront distribution
3. Configure Django to use S3 backend (django-storages)

```python
# settings/production.py
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

### Bunny CDN

**Pros:**
- Very affordable
- Good performance
- Simple pricing

**Cons:**
- Less feature-rich than Cloudflare
- Smaller network

**Setup:**
Similar to Cloudflare but with pull zone configuration.

### Fastly

**Pros:**
- Enterprise-grade
- Real-time purging
- Advanced caching logic

**Cons:**
- Expensive
- Overkill for small projects

## Testing CDN Configuration

### 1. Test Static Files

```bash
# Before CDN
curl -I http://yourdomain.com/static/css/output.css

# After CDN
curl -I https://yourdomain.com/static/css/output.css
```

Check for:
- `cf-cache-status: HIT` (Cloudflare)
- `x-cache: Hit from cloudfront` (CloudFront)
- Appropriate `cache-control` headers

### 2. Performance Testing

Run Lighthouse audit:

```bash
npm run lighthouse:ci
```

Check improvements in:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)

### 3. Cache Hit Rate Monitoring

Add to `apps/core/management/commands/cdn_stats.py`:

```python
from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    help = 'Check CDN cache hit rates'

    def handle(self, *args, **options):
        urls = [
            '/static/css/output.css',
            '/static/js/dist/core.bundle.js',
        ]

        for url in urls:
            response = requests.head(f'https://yourdomain.com{url}')
            cache_status = response.headers.get('cf-cache-status', 'UNKNOWN')
            self.stdout.write(f'{url}: {cache_status}')
```

## Cache Invalidation

### Cloudflare Purge

```python
import requests
from django.conf import settings

def purge_cdn_cache(urls):
    """Purge specific URLs from Cloudflare cache."""
    if not settings.CDN_ENABLED:
        return

    zone_id = settings.CLOUDFLARE_ZONE_ID
    api_token = settings.CLOUDFLARE_API_TOKEN

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }

    data = {
        'files': [f'https://{settings.CDN_DOMAIN}{url}' for url in urls]
    }

    response = requests.post(
        f'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache',
        headers=headers,
        json=data
    )

    return response.json()
```

### Purge on Deploy

Add to your deployment script:

```bash
# After collectstatic
python manage.py collectstatic --noinput

# Purge CDN cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

## Troubleshooting

### Static Files Not Loading

1. Check DNS propagation: `nslookup yourdomain.com`
2. Verify STATIC_URL in Django settings
3. Check Cloudflare SSL/TLS mode (should be "Full" or "Full (strict)")
4. Verify cache rules are correctly configured

### Cache Not Working

1. Check response headers: `curl -I https://yourdomain.com/static/css/output.css`
2. Verify cache rules in Cloudflare
3. Check that files have proper versioning/hashing
4. Ensure WhiteNoise is properly configured

### Mixed Content Warnings

If you see mixed content warnings:
1. Ensure all static file references use HTTPS
2. Check `SECURE_PROXY_SSL_HEADER` is set correctly
3. Verify Cloudflare SSL/TLS mode

## Performance Benchmarks

Expected improvements with CDN:

- **Without CDN:**
  - TTFB: 200-500ms
  - Load Time: 2-4s
  - Bandwidth: 2-5 MB/page

- **With CDN:**
  - TTFB: 50-100ms (edge cache hit)
  - Load Time: 0.5-1.5s
  - Bandwidth: Offloaded to CDN

## Monitoring

### Cloudflare Analytics

Access in Cloudflare dashboard:
- Total requests
- Bandwidth saved
- Cache hit ratio
- Threats blocked

### Custom Monitoring

```python
# apps/core/middleware/cdn_monitoring.py
import time
from django.utils.deprecation import MiddlewareMixin

class CDNPerformanceMonitor(MiddlewareMixin):
    def process_request(self, request):
        request.cdn_start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'cdn_start_time'):
            duration = time.time() - request.cdn_start_time
            response['X-Response-Time'] = f'{duration:.3f}s'
        return response
```

## Best Practices

1. **Version Static Files**: Use WhiteNoise's manifest storage for cache-busting
2. **Set Long Cache Times**: Static files should cache for 1 year
3. **Compress Everything**: Enable Brotli/Gzip compression
4. **Use WebP Images**: Convert images to WebP format
5. **Monitor Cache Hit Rate**: Aim for >90% cache hit rate
6. **Purge on Deploy**: Clear CDN cache after deployments
7. **Test Thoroughly**: Verify all static files load correctly

## Security Considerations

1. **SSL/TLS**: Always use HTTPS
2. **CORS Headers**: Configure if serving from different domain
3. **Access Control**: Restrict admin/API endpoints
4. **Rate Limiting**: Use Cloudflare's rate limiting features
5. **DDoS Protection**: Enable Cloudflare's DDoS protection

## Cost Estimates

### Cloudflare (Recommended for start)
- **Free Tier**: $0/month
  - Unlimited bandwidth
  - Basic DDoS protection
  - Shared SSL certificate
  - Perfect for most projects

### AWS CloudFront
- **Estimated Cost**: $5-50/month
  - $0.085/GB transfer
  - 10,000 requests free tier
  - Pay-as-you-go model

### Bunny CDN
- **Estimated Cost**: $1-10/month
  - $0.01-0.03/GB depending on region
  - Very cost-effective

## Next Steps

1. [x] Set up Cloudflare account
2. [x] Configure DNS
3. [x] Enable cache rules
4. [x] Update Django settings
5. [x] Test static files loading
6. [x] Run performance benchmarks
7. [x] Monitor cache hit rates
8. [ ] Configure cache invalidation on deploy

## References

- [Cloudflare Documentation](https://developers.cloudflare.com/)
- [Django WhiteNoise Documentation](http://whitenoise.evans.io/)
- [Web.dev CDN Guide](https://web.dev/content-delivery-networks/)
- [CloudFlare Page Rules](https://support.cloudflare.com/hc/en-us/articles/218411427)
