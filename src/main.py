#!/usr/bin/env python3
import argparse
import asyncio
import os
from pathlib import Path
from typing import Any, Optional

import uvicorn
from contextlib import asynccontextmanager

from .app import app
from .config import (
    logger, download_dir, rabbitmq_host, rabbitmq_port, rabbitmq_user,
    rabbitmq_password, rabbitmq_queue, rabbitmq_vhost,
    rabbitmq_use_ssl
)
from .plex import setup_plex
from .rabbitmq import RabbitMQConsumer, AIO_PIKA_AVAILABLE


# This will be our shared state for global variables
class AppState:
    def __init__(self) -> None:
        self.consumer: Optional[Any] = None
        self.shutdown_event = asyncio.Event()


app_state = AppState()


@asynccontextmanager
async def lifespan(app: Any) -> Any:
    # Startup: Create and start the RabbitMQ consumer
    if AIO_PIKA_AVAILABLE:
        consumer = app_state.consumer = RabbitMQConsumer(
            host=rabbitmq_host,
            port=rabbitmq_port,
            username=rabbitmq_user,
            password=rabbitmq_password,
            queue_name=rabbitmq_queue,
            vhost=rabbitmq_vhost,
            use_ssl=rabbitmq_use_ssl
        )

        # Start consumer in a separate task
        asyncio.create_task(consumer.run_consumer())
        logger.info(f"RabbitMQ consumer started for {rabbitmq_host}:{rabbitmq_port} (SSL: {rabbitmq_use_ssl})")
    else:
        logger.warning("RabbitMQ support is disabled. Install aio-pika to enable it.")

    yield

    # Shutdown: Stop the RabbitMQ consumer
    consumer = app_state.consumer  # type: ignore
    if consumer and AIO_PIKA_AVAILABLE:
        logger.info("Stopping RabbitMQ consumer...")
        await consumer.stop()
        logger.info("RabbitMQ consumer stopped")


# Add the lifespan handler to the app
app.router.lifespan_context = lifespan


async def start_fastapi(host: str, port: int) -> None:
    """Start the FastAPI application with uvicorn."""
    config = uvicorn.Config(app, host=host, port=port, lifespan="on")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Media Downloader API")
    parser.add_argument(
        "--download-dir",
        type=str,
        default=os.environ.get("DOWNLOAD_DIR", "./.downloads"),
        help="Directory to save downloaded files (default: ./.downloads or DOWNLOAD_DIR env var)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )

    # RabbitMQ arguments only if aio_pika is available
    if AIO_PIKA_AVAILABLE:
        parser.add_argument(
            "--rabbitmq-host",
            type=str,
            default=rabbitmq_host,
            help=f"RabbitMQ host (default: {rabbitmq_host} or RABBITMQ_HOST env var)"
        )
        parser.add_argument(
            "--rabbitmq-port",
            type=int,
            default=rabbitmq_port,
            help=f"RabbitMQ port (default: {rabbitmq_port} or RABBITMQ_PORT env var)"
        )
        parser.add_argument(
            "--rabbitmq-user",
            type=str,
            default=rabbitmq_user,
            help=f"RabbitMQ username (default: {rabbitmq_user} or RABBITMQ_USER env var)"
        )
        parser.add_argument(
            "--rabbitmq-password",
            type=str,
            default=rabbitmq_password,
            help="RabbitMQ password (default: masked or RABBITMQ_PASSWORD env var)"
        )
        parser.add_argument(
            "--rabbitmq-queue",
            type=str,
            default=rabbitmq_queue,
            help=f"RabbitMQ queue name (default: {rabbitmq_queue} or RABBITMQ_QUEUE env var)"
        )
        parser.add_argument(
            "--rabbitmq-vhost",
            type=str,
            default=rabbitmq_vhost,
            help=f"RabbitMQ virtual host (default: {rabbitmq_vhost} or RABBITMQ_VHOST env var)"
        )
        parser.add_argument(
            "--rabbitmq-use-ssl",
            action="store_true",
            default=rabbitmq_use_ssl,
            help=f"Use SSL for RabbitMQ connection (default: {rabbitmq_use_ssl} or RABBITMQ_USE_SSL env var)"
        )

    args = parser.parse_args()

    # Set up download directory
    args_download_dir = Path(args.download_dir)
    args_download_dir.mkdir(parents=True, exist_ok=True)

    # Set up Plex integration
    from .config import plex_server
    plex_server = setup_plex()

    # Update environment variables for RabbitMQ if available
    if AIO_PIKA_AVAILABLE and hasattr(args, 'rabbitmq_host'):
        os.environ["RABBITMQ_HOST"] = args.rabbitmq_host
        os.environ["RABBITMQ_PORT"] = str(args.rabbitmq_port)
        os.environ["RABBITMQ_USER"] = args.rabbitmq_user
        os.environ["RABBITMQ_PASSWORD"] = args.rabbitmq_password
        os.environ["RABBITMQ_QUEUE"] = args.rabbitmq_queue
        os.environ["RABBITMQ_VHOST"] = args.rabbitmq_vhost
        os.environ["RABBITMQ_USE_SSL"] = str(args.rabbitmq_use_ssl).lower()

        if args.rabbitmq_use_ssl:
            logger.info(f"RabbitMQ configured at {args.rabbitmq_host}:{args.rabbitmq_port} with SSL, queue: {args.rabbitmq_queue}")
        else:
            logger.info(f"RabbitMQ configured at {args.rabbitmq_host}:{args.rabbitmq_port}, queue: {args.rabbitmq_queue}")

    logger.info(f"Starting server, download directory set to: {args_download_dir}")

    # Run the FastAPI application
    asyncio.run(start_fastapi(args.host, args.port))


if __name__ == "__main__":
    main()
