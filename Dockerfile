FROM python:3.9-slim

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory and set permissions
RUN mkdir -p app/static/uploads && \
    chmod -R 777 app/static/uploads && \
    chmod 777 /app && \
    touch /tmp/images.db && \
    chmod 777 /tmp/images.db

# Create uploads directory
RUN mkdir -p app/static/uploads && chmod 777 app/static/uploads

# Set environment variables
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run as non-root user for better security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app

USER appuser

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
