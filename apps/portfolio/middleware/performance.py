from django.utils.deprecation import MiddlewareMixin


class PerformanceMiddleware(MiddlewareMixin):
    """Performance monitoring and optimization middleware"""

    def process_request(self, request):
        # Add request start time for performance monitoring
        import time

        request._performance_start = time.time()
        return None

    def process_response(self, request, response):
        # Calculate request processing time
        if hasattr(request, "_performance_start"):
            import time

            processing_time = time.time() - request._performance_start
            response["X-Response-Time"] = f"{processing_time:.3f}s"

        # Add performance hints
        response["X-DNS-Prefetch-Control"] = "on"
        response["X-Preload"] = "dns-prefetch"

        return response
