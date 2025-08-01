#!/usr/bin/env python3
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plexapi.server import PlexServer
else:
    PlexServer = Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup error log file
error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler(os.getenv("ERROR_LOG_FILE", "download_errors.log"))
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

# Global configuration
download_dir: Path = Path(os.getenv("DOWNLOAD_DIR", "./.downloads"))
plex_library: str = os.getenv("PLEX_LIBRARY", "Home Videos")

# Try to import PlexAPI if available
try:
    from plexapi.server import PlexServer as _PlexServer
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False
    _PlexServer = None

plex_server: Optional['PlexServer'] = None


def parse_amqp_url(url: str) -> Dict[str, Any]:
    """Parse an AMQP URL into components for RabbitMQ connection.

    Handles both standard AMQP URLs and CloudAMQP-style URLs.

    Args:
        url: AMQP URL string (e.g., amqp://user:pass@host:port/vhost)

    Returns:
        Dictionary with host, port, username, password, vhost, and ssl flag
    """
    if not url:
        return {}

    # Check if it's already a properly formatted URL
    if not url.startswith(('amqp://', 'amqps://')):
        url = f"amqp://{url}"

    try:
        parsed = urllib.parse.urlparse(url)

        # Determine if SSL should be used
        use_ssl = parsed.scheme == 'amqps'

        # Get port (default to 5672 for non-SSL, 5671 for SSL)
        port = parsed.port or (5671 if use_ssl else 5672)

        # Parse username and password
        username = urllib.parse.unquote(parsed.username) if parsed.username else 'guest'
        password = urllib.parse.unquote(parsed.password) if parsed.password else 'guest'

        # Parse vhost (default to '/')
        vhost = parsed.path
        if not vhost:
            vhost = '/'
        # Remove leading slash as some clients require it without the slash
        elif vhost.startswith('/'):
            vhost = vhost[1:] or '/'

        # Handle special case where vhost is URL encoded
        vhost = urllib.parse.unquote(vhost)

        return {
            'host': parsed.hostname or 'localhost',
            'port': port,
            'username': username or 'guest',
            'password': password or 'guest',
            'vhost': vhost,
            'use_ssl': use_ssl
        }
    except Exception as e:
        logger.error(f"Failed to parse AMQP URL: {e}")
        return {}


# Try to get RabbitMQ config from URL first
rabbitmq_url = os.getenv("RABBITMQ_URL")
rabbitmq_config = parse_amqp_url(rabbitmq_url) if rabbitmq_url else {}
logger.debug(rabbitmq_url)
logger.debug(rabbitmq_config)

# RabbitMQ configuration (fall back to individual settings if URL not provided)
rabbitmq_host: str = str(rabbitmq_config.get('host') or os.getenv("RABBITMQ_HOST", "localhost"))
rabbitmq_port: int = int(str(rabbitmq_config.get('port') or os.getenv("RABBITMQ_PORT", "5672")))
rabbitmq_user: str = str(rabbitmq_config.get('username') or os.getenv("RABBITMQ_USER", "guest"))
rabbitmq_password: str = str(rabbitmq_config.get('password') or os.getenv("RABBITMQ_PASSWORD", "guest"))
rabbitmq_queue: str = os.getenv("RABBITMQ_QUEUE", "music")
rabbitmq_vhost: str = str(rabbitmq_config.get('vhost') or os.getenv("RABBITMQ_VHOST", "/"))
rabbitmq_use_ssl: bool = bool(rabbitmq_config.get('use_ssl') or os.getenv("RABBITMQ_USE_SSL", "false").lower() in ("true", "1", "yes"))

# Detect CloudAMQP automatically
if "cloudamqp.com" in rabbitmq_host:
    logger.info("CloudAMQP detected, enabling SSL automatically")
    # CloudAMQP typically uses SSL on port 5671
    if rabbitmq_port == 5672:
        rabbitmq_port = 5671
    rabbitmq_use_ssl = True

# Log configuration for debugging
logger.info(f"RabbitMQ configuration: {rabbitmq_host}:{rabbitmq_port}, vhost: {rabbitmq_vhost}")
if rabbitmq_use_ssl:
    logger.info("Using SSL for RabbitMQ connection")
