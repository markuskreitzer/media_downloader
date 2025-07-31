FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src

# Create downloads directory
RUN mkdir -p ./.downloads && chmod 777 ./.downloads

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DOWNLOAD_DIR=/.downloads

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]
