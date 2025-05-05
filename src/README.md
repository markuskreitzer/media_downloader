# Media Downloader API

This is a refactored version of the original `download_api.py` file, split into multiple modules for better organization and maintainability. It now supports both FastAPI HTTP endpoints and RabbitMQ queue processing for download requests.

## Project Structure

- **config.py**: Contains configuration variables, logging setup, and global state
- **models.py**: Defines Pydantic models for request/response validation
- **utils.py**: Utility functions like filename sanitization
- **plex.py**: Plex media server integration functionality
- **routes.py**: API endpoint handlers with business logic
- **app.py**: FastAPI application setup and route definitions
- **rabbitmq.py**: RabbitMQ consumer for processing download requests from a queue
- **main.py**: Entry point for running the application with both HTTP and RabbitMQ support
- **send_test_message.py**: Utility script for testing RabbitMQ integration

## Running the Application

```bash
python -m src.main --download-dir /path/to/downloads --host 0.0.0.0 --port 8000 \
    --rabbitmq-host localhost --rabbitmq-port 5672 --rabbitmq-user guest \
    --rabbitmq-password guest --rabbitmq-queue download_requests
```

## Environment Variables

- `DOWNLOAD_DIR`: Directory to save downloaded files
- `PLEX_URL`: URL of the Plex server (optional)
- `PLEX_TOKEN`: Authentication token for Plex (optional)
- `PLEX_LIBRARY`: Name of the Plex library to scan (default: "Home Videos")
- `RABBITMQ_HOST`: Hostname of the RabbitMQ server (default: localhost)
- `RABBITMQ_PORT`: Port of the RabbitMQ server (default: 5672)
- `RABBITMQ_USER`: Username for RabbitMQ authentication (default: guest)
- `RABBITMQ_PASSWORD`: Password for RabbitMQ authentication (default: guest)
- `RABBITMQ_QUEUE`: Name of the queue to consume messages from (default: download_requests)
- `RABBITMQ_VHOST`: RabbitMQ virtual host (default: /)

## Using the API

### HTTP Endpoint

Send a POST request to `/download/` with a JSON body:

```json
{
  "url": "https://example.com/video.mp4"
}
```

### RabbitMQ Queue

Send a message to the configured RabbitMQ queue with the following JSON format:

```json
{
  "url": "https://example.com/video.mp4"
}
```

You can use the included utility script to send a test message:

```bash
python -m src.send_test_message "https://example.com/video.mp4"
```

## Dependencies

- FastAPI
- Pydantic
- yt-dlp
- aio_pika (for RabbitMQ consumer)
- pika (for test message utility)
- PlexAPI (optional, for Plex integration)
