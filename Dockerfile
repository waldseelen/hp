FROM python:3.11-slim


# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY portfolio_site/ ./portfolio_site/

# Set working directory to portfolio_site
WORKDIR /app/portfolio_site

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=portfolio_site.settings

# Expose port
EXPOSE 8000

# Run migrations, collect static files and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn portfolio_site.wsgi:application --bind 0.0.0.0:$PORT"]
