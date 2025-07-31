# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Using uv (Recommended)

```bash
# Install dependencies
uv sync --all-extras

# Run locally with default settings
uv run python -m src.main

# Run with custom settings
uv run python -m src.main --download-dir ./downloads --host 0.0.0.0 --port 8000

# Or use the installed script
uv run media-downloader

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_routes.py

# Run with coverage
uv run pytest --cov=src

# Run linting
uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
uv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code with black
uv run black src tests

# Type checking
uv run mypy src

# Send test message to RabbitMQ
uv run python -m src.send_test_message "https://example.com/video.mp4"
uv run send-test-message "https://example.com/video.mp4" --media-type audio
```

### Without uv (Standard Python)

```bash
# Run locally with default settings
python -m src.main

# Run with custom settings
python -m src.main --download-dir ./downloads --host 0.0.0.0 --port 8000

# Run tests
pytest

# Send test message to RabbitMQ
python -m src.send_test_message "https://example.com/video.mp4"
```

### Docker

```bash
# Run with Docker
docker-compose up -d

# Build Docker image
docker build -t media-downloader .
```

## Architecture Overview

### Core Components

1. **FastAPI Application (`src/app.py`, `src/main.py`)**
   - Entry point: `src/main.py` - Handles CLI arguments, configures the app, and starts the server
   - App definition: `src/app.py` - Defines the FastAPI app instance and main endpoint
   - Uses lifespan context manager to start/stop RabbitMQ consumer

2. **Configuration (`src/config.py`)**
   - Loads environment variables from `.env` file using python-dotenv
   - Parses AMQP URLs for RabbitMQ configuration
   - Automatically detects CloudAMQP and enables SSL
   - Manages global settings: download directory, Plex config, RabbitMQ settings

3. **Download Processing (`src/routes.py`)**
   - Core function: `download_media()` - Uses yt-dlp to download media
   - Sanitizes filenames and sets file permissions (777) for NAS compatibility
   - Triggers Plex library scan after successful download
   - Error handling with proper logging to error log file

4. **RabbitMQ Integration (`src/rabbitmq.py`)**
   - `RabbitMQConsumer` class handles async message processing
   - Supports both standard and SSL connections (auto-detected for CloudAMQP)
   - Robust connection with automatic reconnection
   - Processes messages containing URLs for download

5. **Models (`src/models.py`)**
   - Pydantic models for request validation
   - `DownloadRequest` model validates URL format

6. **Utilities (`src/utils.py`)**
   - Filename sanitization functions
   - Helper utilities for file operations

7. **Plex Integration (`src/plex.py`)**
   - Optional integration with Plex Media Server
   - Triggers library scans after downloads

### Message Flow

1. **HTTP Endpoint**: POST to `/download/` → `download_media()` → yt-dlp download → Plex scan
2. **RabbitMQ**: Message in queue → `RabbitMQConsumer.process_message()` → `download_media()` → yt-dlp download → Plex scan

### Key Dependencies

- **Required**: fastapi, uvicorn, pydantic, yt-dlp, python-dotenv
- **Optional**: aio-pika (RabbitMQ), plexapi (Plex integration)
- The app gracefully handles missing optional dependencies

### Environment Configuration

The app uses environment variables (or `.env` file) for configuration:
- `DOWNLOAD_DIR`: Where to save downloaded files
- `RABBITMQ_URL` or individual RabbitMQ settings
- `PLEX_URL`, `PLEX_TOKEN`, `PLEX_LIBRARY` for Plex integration
- `ERROR_LOG_FILE`: Path for error logging

### Docker Deployment

- Multi-stage Dockerfile for optimized image size
- GitHub Actions workflow for automatic Docker image builds and publishing to ghcr.io
- Docker Compose configuration for easy deployment