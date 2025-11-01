from django.utils.deprecation import MiddlewareMixin


class CompressionMiddleware(MiddlewareMixin):
    """Additional compression settings"""

    def process_response(self, request, response):
        # Add Vary header for better caching
        vary_headers = (
            response.get("Vary", "").split(", ") if response.get("Vary") else []
        )

        # Add encoding to vary for compressed responses
        if "Accept-Encoding" not in vary_headers:
            vary_headers.append("Accept-Encoding")

        # Add User-Agent for mobile optimization
        if "User-Agent" not in vary_headers:
            vary_headers.append("User-Agent")

        response["Vary"] = ", ".join(filter(None, vary_headers))

        return response
