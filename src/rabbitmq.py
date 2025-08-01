#!/usr/bin/env python3
import asyncio
import json
import ssl
from typing import Optional, Any

# Try to import aio_pika, but don't fail if it's not available
try:
    import aio_pika
    AIO_PIKA_AVAILABLE = True
except ImportError:
    AIO_PIKA_AVAILABLE = False

from .config import logger, error_logger
from .models import DownloadRequest, VideoDownloadRequest, AudioDownloadRequest, PictureDownloadRequest, MediaType
from .routes import download_media, download_video, download_audio, download_picture


class RabbitMQConsumer:
    """Consumer for processing download requests from RabbitMQ."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        queue_name: str = "download_requests",
        vhost: str = "/",
        use_ssl: bool = False
    ):
        if not AIO_PIKA_AVAILABLE:
            logger.warning("aio_pika not installed. RabbitMQ consumer will not be available.")
            logger.warning("To enable RabbitMQ support, install the required package with: pip install aio-pika")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue_name = queue_name
        self.vhost = vhost
        self.use_ssl = use_ssl
        self.connection: Optional[Any] = None
        self.channel: Optional[Any] = None
        self.queue: Optional[Any] = None
        self.running = False

    async def connect(self) -> bool:
        """Establish connection to RabbitMQ server."""
        if not AIO_PIKA_AVAILABLE:
            error_logger.error("Cannot connect to RabbitMQ: aio_pika package is not installed")
            return False

        try:
            # Determine if we need SSL context
            ssl_options = None
            if self.use_ssl or self.port == 5671:
                ssl_context = ssl.create_default_context()
                # For development/testing, you might want to disable hostname verification
                # ssl_context.check_hostname = False
                # ssl_context.verify_mode = ssl.CERT_NONE
                ssl_options = {"ssl": ssl_context}
                logger.info("Using SSL for RabbitMQ connection")

            # Build correct URL format with percent encoding for special characters in password
            amqp_protocol = "amqps" if self.use_ssl or self.port == 5671 else "amqp"
            if self.vhost and not self.vhost.startswith("/"):
                self.vhost = f"/{self.vhost}"

            connection_string = f"{amqp_protocol}://{self.username}:{self.password}@{self.host}:{self.port}{self.vhost}"

            # Connect with robust connection (automatic reconnection)
            self.connection = await aio_pika.connect_robust(
                connection_string,
                client_properties={
                    "connection_name": "media-downloader-consumer"
                },
                **ssl_options if ssl_options else {}
            )

            logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            # Declare queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            logger.info(f"Queue {self.queue_name} declared")
            return True

        except aio_pika.exceptions.AMQPConnectionError as e:
            if "ACCESS_REFUSED" in str(e):
                error_logger.error(f"Authentication failed for RabbitMQ: Invalid credentials or vhost '{self.vhost}'")
                logger.error("RabbitMQ authentication error: Check your username, password, and vhost configuration")
                logger.error("For CloudAMQP, make sure you're using the correct AMQP URL from your CloudAMQP instance dashboard")
            else:
                error_logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
        except Exception as e:
            error_logger.error(f"Unexpected error connecting to RabbitMQ: {e}")
            return False

    async def process_message(self, message: Any) -> None:
        """Process incoming message from RabbitMQ."""
        if not AIO_PIKA_AVAILABLE:
            return

        async with message.process():
            try:
                body = message.body.decode()
                logger.info(f"Received message from RabbitMQ: {body}")

                # Parse the message
                data = json.loads(body)
                url = data.get("url")
                media_type = data.get("media_type", "video")  # Default to video for backward compatibility

                if not url:
                    logger.warning("Message missing 'url' field")
                    return

                # Create appropriate download request based on media type
                try:
                    if media_type == MediaType.AUDIO or media_type == "audio":
                        audio_request = AudioDownloadRequest(url=url)
                        result = await download_audio(audio_request)
                    elif media_type == MediaType.PICTURE or media_type == "picture":
                        picture_request = PictureDownloadRequest(url=url)
                        result = await download_picture(picture_request)
                    elif media_type == MediaType.VIDEO or media_type == "video":
                        video_request = VideoDownloadRequest(url=url)
                        result = await download_video(video_request)
                    else:
                        # Fall back to legacy endpoint for unknown types
                        general_request = DownloadRequest(url=url)
                        result = await download_media(general_request)

                    logger.info(f"Download completed: {result}")

                except Exception as e:
                    error_logger.error(f"Invalid URL format: {url}, Error: {str(e)}")

            except json.JSONDecodeError:
                error_logger.error(f"Invalid JSON in message: {body}")
            except Exception as e:
                error_logger.error(f"Error processing message: {str(e)}")

    async def start_consuming(self) -> None:
        """Start consuming messages from the queue."""
        if not AIO_PIKA_AVAILABLE:
            logger.warning("Cannot start consuming: aio_pika package is not installed")
            return

        if not self.connection or self.connection.is_closed:
            if not await self.connect():
                return

        self.running = True

        if self.queue is None:
            logger.error("Queue is not initialized")
            return

        async with self.queue.iterator() as queue_iter:
            logger.info(f"Started consuming from queue {self.queue_name}")
            async for message in queue_iter:
                if not self.running:
                    break
                await self.process_message(message)

    async def stop(self) -> None:
        """Stop the consumer and close connections."""
        if not AIO_PIKA_AVAILABLE:
            return

        self.running = False

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection")

    async def run_consumer(self) -> None:
        """Run the consumer with reconnection logic."""
        if not AIO_PIKA_AVAILABLE:
            logger.warning("Cannot run RabbitMQ consumer: aio_pika package is not installed")
            await asyncio.sleep(3600)  # Just sleep for an hour to keep the task alive
            return

        self.running = True

        while self.running:
            try:
                if await self.connect():
                    await self.start_consuming()
                else:
                    # If connection failed, wait before retry
                    logger.warning(f"Failed to connect to RabbitMQ at {self.host}:{self.port}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
            except Exception as e:
                error_logger.error(f"Unexpected error in RabbitMQ consumer: {str(e)}")
                logger.warning("RabbitMQ consumer error. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)  # Wait before reconnection attempt
