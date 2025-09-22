#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings.development')
django.setup()

from django.core.wsgi import get_wsgi_application
from wsgiref.simple_server import make_server

print("Starting test server...")
application = get_wsgi_application()
print("WSGI application created successfully")

# Create and start server
with make_server('localhost', 8000, application) as httpd:
    print("Server started on http://localhost:8000")
    print("Press Ctrl+C to stop...")
    httpd.serve_forever()