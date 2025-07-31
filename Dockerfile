# Multi-stage build for smaller final image
FROM python:3.11-alpine AS builder

LABEL org.opencontainers.image.description "A Python API service for downloading media from URLs via HTTP endpoints and RabbitMQ messaging with yt-dlp"

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    g++

# Upgrade pip
RUN pip install --upgrade pip

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install dependencies (only rabbitmq extras, plex is optional)
RUN pip install --no-cache-dir .[rabbitmq]

# Final stage
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache ffmpeg

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src ./src

# Create downloads directory
RUN mkdir -p /downloads && chmod 777 /downloads

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DOWNLOAD_DIR=/downloads

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]
