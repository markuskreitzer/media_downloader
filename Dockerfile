# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install dependencies (only rabbitmq extras, plex is optional)
RUN pip install --no-cache-dir .[rabbitmq]

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

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
