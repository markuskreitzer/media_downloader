# Media Downloader API

A Python API service for downloading media from URLs via HTTP endpoints and RabbitMQ messaging.

## Features

- Download media from URLs using yt-dlp
- HTTP API endpoint for direct requests
- RabbitMQ integration for asynchronous processing
- Plex Media Server integration for automatic library updates
- Environment variable configuration with dotenv support

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
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=download_requests
RABBITMQ_VHOST=/
RABBITMQ_USE_SSL=false
```

### CloudAMQP Configuration

If you're using CloudAMQP, use the following configuration:

```
RABBITMQ_HOST=yourinstance.rmq.cloudamqp.com
RABBITMQ_PORT=5671
RABBITMQ_USER=yourusername
RABBITMQ_PASSWORD=yourpassword
RABBITMQ_VHOST=yourvhost
RABBITMQ_USE_SSL=true
```

The application will automatically detect CloudAMQP hostnames and enable SSL.

## Running the Application

Start the application with default settings:

```bash
python -m src.main
```

Or with custom settings:

```bash
python -m src.main --download-dir ./downloads --host 0.0.0.0 --port 8000
```

## Using the API

### HTTP Endpoint

Send a POST request to `/download/` with a JSON body:

```json
{
  "url": "https://example.com/video.mp4"
}
```

Example using curl:

```bash
curl -X POST http://localhost:8000/download/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/video.mp4"}'
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

## Troubleshooting

### RabbitMQ Connection Issues

If you're experiencing RabbitMQ connection issues:

1. Check that your credentials and vhost are correct
2. For CloudAMQP, make sure SSL is enabled (`RABBITMQ_USE_SSL=true`)
3. Verify that the port is set to 5671 for SSL connections
4. Check your CloudAMQP console for connection limits or other restrictions

## Optional Dependencies

- **aio-pika**: Required for RabbitMQ consumer functionality
- **pika**: Required for the send_test_message utility
- **plexapi**: Required for Plex integration

If these packages are not installed, the corresponding features will be disabled with appropriate warnings.
