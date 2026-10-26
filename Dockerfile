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
RUN python -m pip install --upgrade "pip>=26.2.2"

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

# Create directories
RUN mkdir -p /downloads /tmp/cookies /var/log && chmod 777 /downloads /tmp/cookies /var/log

# Copy update script
COPY scripts/update-ytdlp.sh /usr/local/bin/update-ytdlp.sh
RUN chmod +x /usr/local/bin/update-ytdlp.sh

# Set up cron for daily updates
RUN echo "0 3 * * * /usr/local/bin/update-ytdlp.sh >> /var/log/yt-dlp-update.log 2>&1" | crontab -

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DOWNLOAD_DIR=/downloads

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]
