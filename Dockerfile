# Andre - Collaborative Music Queue System
# Python 3 Docker image

FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and oauth
RUN mkdir -p /app/play_logs /app/oauth_creds

# Expose the application port
EXPOSE 5000

# Default environment variables
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV DEBUG=false

# Run the application
CMD ["python", "run.py"]
