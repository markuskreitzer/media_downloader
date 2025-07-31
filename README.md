# Media Downloader API

A Python API service for downloading media from URLs via HTTP endpoints and RabbitMQ messaging.

## Features

- Download media from URLs using yt-dlp
- Separate endpoints for video, audio, and picture downloads
- Automatic file organization based on metadata (artist/album for audio, channel/series for video)
- HTTP API endpoints for direct requests
- RabbitMQ integration for asynchronous processing
- Plex Media Server integration for automatic library updates
- Environment variable configuration with dotenv support
- Docker support for easy deployment

## Project Structure

- **src/config.py**: Configuration variables and environment setup
- **src/models.py**: Pydantic models for request validation
- **src/utils.py**: Utility functions like filename sanitization
- **src/plex.py**: Plex media server integration
- **src/routes.py**: API endpoint handlers
- **src/app.py**: FastAPI application setup
- **src/rabbitmq.py**: RabbitMQ consumer for processing download requests
- **src/main.py**: Application entry point
- **src/send_test_message.py**: Utility for testing RabbitMQ integration

## Installation

### Using uv (Recommended)

1. Clone the repository
2. Install uv if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies with uv:

```bash
# Install all dependencies (including optional ones)
uv sync --all-extras

# Or install only core dependencies
uv sync

# Or install with specific extras
uv sync --extra rabbitmq --extra plex --extra dev

# Available extras:
# - rabbitmq: RabbitMQ integration (aio-pika, pika)  
# - plex: Plex Media Server integration (plexapi)
# - dev: Development tools (pytest, black, mypy, etc.)
```

4. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration values.

### Standard Installation (pip)

1. Clone the repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

4. Edit the `.env` file with your configuration values.

### Docker Installation

You can run the application using Docker:

```bash
# Build and run using Docker Compose
docker-compose up -d

# Or pull from GitHub Container Registry
docker pull ghcr.io/yourusername/media-downloader:latest
docker run -p 8000:8000 -v downloads:/downloads -e RABBITMQ_URL=amqp://user:pass@host:port/vhost ghcr.io/yourusername/media-downloader:latest
```

## Configuration

The application can be configured through environment variables or a `.env` file:

```
# Download API Configuration
DOWNLOAD_DIR=./.downloads

# Plex Integration
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your-plex-token
PLEX_LIBRARY=Home Videos

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F
RABBITMQ_QUEUE=download_requests
```

### CloudAMQP Configuration

If you're using CloudAMQP, the easiest way to configure it is to copy the AMQP URL from your CloudAMQP dashboard and set it in your .env file:

```
# Using the full AMQP URL (recommended for CloudAMQP)
RABBITMQ_URL=amqps://yourusername:yourpassword@host.rmq.cloudamqp.com/yourvhost

# You still need to specify the queue name
RABBITMQ_QUEUE=download_requests
```

Alternatively, you can split the settings into individual components:

```
RABBITMQ_HOST=yourinstance.rmq.cloudamqp.com
RABBITMQ_PORT=5671
RABBITMQ_USER=yourusername
RABBITMQ_PASSWORD=yourpassword
RABBITMQ_VHOST=yourvhost
RABBITMQ_USE_SSL=true
RABBITMQ_QUEUE=download_requests
```

The application will automatically detect CloudAMQP hostnames and enable SSL.

## Running the Application

### Running Locally with uv

Start the application with default settings:

```bash
uv run python -m src.main
```

Or with custom settings:

```bash
uv run python -m src.main --download-dir ./downloads --host 0.0.0.0 --port 8000
```

Or use the installed script:

```bash
uv run media-downloader
```

### Running Locally with standard Python

Start the application with default settings:

```bash
python -m src.main
```

Or with custom settings:

```bash
python -m src.main --download-dir ./downloads --host 0.0.0.0 --port 8000
```

### Running with Docker

```bash
# Using Docker directly
docker run -p 8000:8000 -e RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/ ghcr.io/yourusername/media-downloader:latest

# Using Docker Compose
docker-compose up -d
```

## CI/CD Pipeline

This project includes a GitHub Actions workflow to automatically build and publish Docker images to GitHub Container Registry (ghcr.io) when:

1. Pushing to the main/master branch
2. Creating a release tag (v*)
3. Opening a pull request

To set up the CI/CD pipeline:

1. Ensure your repository has the necessary permissions to write packages
2. Push your code to GitHub
3. The GitHub Actions workflow will automatically build and publish the image

## Using the API

### HTTP Endpoints

The API provides separate endpoints for different media types:

#### Video Download
Send a POST request to `/download/video` with a JSON body:

```json
{
  "url": "https://example.com/video.mp4"
}
```

Example using curl:
```bash
curl -X POST http://localhost:8000/download/video \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/video.mp4"}'
```

#### Audio Download
Send a POST request to `/download/audio` with a JSON body:

```json
{
  "url": "https://example.com/audio.mp3"
}
```

Example using curl:
```bash
curl -X POST http://localhost:8000/download/audio \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/audio.mp3"}'
```

#### Picture Download
Send a POST request to `/download/picture` with a JSON body:

```json
{
  "url": "https://example.com/image.jpg"
}
```

Example using curl:
```bash
curl -X POST http://localhost:8000/download/picture \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/image.jpg"}'
```

#### Legacy Endpoint
The original `/download/` endpoint is still available for backward compatibility:

```bash
curl -X POST http://localhost:8000/download/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/video.mp4"}'
```

### RabbitMQ Queue

Send a message to the configured RabbitMQ queue with the following JSON format:

```json
{
  "url": "https://example.com/video.mp4",
  "media_type": "video"  // Optional: "video", "audio", or "picture" (defaults to "video")
}
```

You can use the included utility script to send a test message:

```bash
python -m src.send_test_message "https://example.com/video.mp4"
```

### File Organization

Downloaded files are automatically organized based on their type and metadata:

- **Audio files**: `<download_dir>/audio/<artist>/<album>/<title>.mp3`
  - If no album info: `<download_dir>/audio/<artist>/<title>.mp3`
- **Video files**: `<download_dir>/video/<channel>/<series>/<title>.mp4`
  - If no series info: `<download_dir>/video/<channel>/<title>.mp4`
  - Music videos with artist metadata are organized like audio files
- **Pictures**: `<download_dir>/pictures/<title>.<ext>`

### iOS Shortcuts Integration

The separate endpoints are designed to work with iOS Shortcuts share sheets:

1. Create a shortcut for video downloads that posts to `/download/video`
2. Create a shortcut for audio downloads that posts to `/download/audio`
3. Add these shortcuts to your share sheet for easy media downloading

## Troubleshooting

### RabbitMQ Connection Issues

If you're experiencing RabbitMQ connection issues:

1. Check that your credentials and vhost are correct
2. For CloudAMQP, make sure SSL is enabled (`RABBITMQ_USE_SSL=true`)
3. Verify that the port is set to 5671 for SSL connections
4. Check your CloudAMQP console for connection limits or other restrictions

### ACCESS_REFUSED Errors

If you see an `ACCESS_REFUSED` error:

1. **Verify credentials**: Double-check your username and password
2. **Check virtual host**: Make sure the virtual host exists and your user has access to it
3. **AMQP URL format**: For CloudAMQP, copy the exact AMQP URL from your CloudAMQP dashboard
4. **URL encoding**: If your password contains special characters, they need to be URL-encoded
5. **Permissions**: Make sure your user has the right permissions for the virtual host

For CloudAMQP, the easiest solution is to use the complete AMQP URL directly from your CloudAMQP dashboard:

```
RABBITMQ_URL=amqps://yourusername:yourpassword@host.rmq.cloudamqp.com/yourvhost
```

## Optional Dependencies

- **aio-pika**: Required for RabbitMQ consumer functionality
- **pika**: Required for the send_test_message utility
- **plexapi**: Required for Plex integration

If these packages are not installed, the corresponding features will be disabled with appropriate warnings.
