# Andre - Collaborative Music Queue System
# Python 3 Docker image with security hardening

# Pin to specific version with digest for reproducibility
FROM python:3.11-slim-bookworm@sha256:549988ff0804593d8373682ef5c0f0ceee48328abaaa2e054241c23f5c324751

# Install system dependencies (including curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd --gid 1000 andre && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home andre

# Copy application code
COPY . .

# Create directories for logs and oauth, set ownership
RUN mkdir -p /app/play_logs /app/oauth_creds && \
    chown -R andre:andre /app

# Switch to non-root user
USER andre

# Expose the application port
EXPOSE 5000

# Default environment variables
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV DEBUG=false

# Run the application
CMD ["python", "run.py"]
