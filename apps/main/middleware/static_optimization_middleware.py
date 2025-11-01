class StaticOptimizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add cache headers for static assets
        if request.path.startswith("/static/"):
            response["Cache-Control"] = "public, max-age=31536000"

        return response
