#!/usr/bin/env python3
"""
Utility script to send a test message to the RabbitMQ queue.

Usage:
    python -m src.send_test_message <url_to_download>
"""

import argparse
import json
import os
import ssl
import sys
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import pika, but don't fail if it's not available
try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False


def parse_amqp_url(url: str):
    """Parse an AMQP URL into components for RabbitMQ connection."""
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
            'username': username,
            'password': password,
            'vhost': vhost,
            'use_ssl': use_ssl
        }
    except Exception as e:
        print(f"Failed to parse AMQP URL: {e}")
        return {}


def send_message(url, host, port, user, password, queue, vhost, use_ssl=False):
    """Send a test message to the RabbitMQ queue."""
    if not PIKA_AVAILABLE:
        print("Error: pika package is not installed.")
        print("To enable RabbitMQ support, install the required package with: pip install pika")
        return False
        
    try:
        # Detect CloudAMQP automatically
        if "cloudamqp.com" in host:
            print("CloudAMQP detected, enabling SSL automatically")
            use_ssl = True
            if port == 5672:
                port = 5671
                
        # Create connection parameters
        credentials = pika.PlainCredentials(user, password)
        ssl_options = None
        
        if use_ssl or port == 5671:
            # Create SSL context for secure connections
            context = ssl.create_default_context()
            # For development/testing, you might want to disable these:
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE
            ssl_options = pika.SSLOptions(context)
            print(f"Using SSL for connection to {host}:{port}")
            
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
            ssl_options=ssl_options
        )
        
        # Connect to RabbitMQ
        print(f"Connecting to RabbitMQ at {host}:{port}, vhost: {vhost}")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queue (this ensures the queue exists)
        channel.queue_declare(queue=queue, durable=True)
        
        # Create message payload
        message = json.dumps({"url": url})
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        
        print(f"Sent message: {message}")
        print(f"To RabbitMQ queue: {queue} on {host}:{port}")
        
        # Close connection
        connection.close()
        return True
        
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False


def main():
    if not PIKA_AVAILABLE:
        print("Error: pika package is not installed.")
        print("To enable RabbitMQ support, install the required package with: pip install pika")
        sys.exit(1)
        
    # Try to get RabbitMQ config from URL first
    rabbitmq_url = os.getenv("RABBITMQ_URL", "")
    rabbitmq_config = parse_amqp_url(rabbitmq_url) if rabbitmq_url else {}
        
    # Get default values from environment variables, with URL taking precedence
    rabbitmq_host = rabbitmq_config.get('host') or os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(rabbitmq_config.get('port') or os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = rabbitmq_config.get('username') or os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password = rabbitmq_config.get('password') or os.getenv("RABBITMQ_PASSWORD", "guest")
    rabbitmq_queue = os.getenv("RABBITMQ_QUEUE", "download_requests")
    rabbitmq_vhost = rabbitmq_config.get('vhost') or os.getenv("RABBITMQ_VHOST", "/")
    rabbitmq_use_ssl = rabbitmq_config.get('use_ssl') or os.getenv("RABBITMQ_USE_SSL", "false").lower() in ("true", "1", "yes")
        
    parser = argparse.ArgumentParser(description="Send a test message to the RabbitMQ download queue")
    parser.add_argument(
        "url",
        type=str,
        help="URL to download"
    )
    parser.add_argument(
        "--amqp-url",
        type=str,
        default=rabbitmq_url,
        help="Full AMQP URL (e.g., amqp://user:pass@host:port/vhost)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=rabbitmq_host,
        help=f"RabbitMQ host (default: {rabbitmq_host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=rabbitmq_port,
        help=f"RabbitMQ port (default: {rabbitmq_port})"
    )
    parser.add_argument(
        "--user",
        type=str,
        default=rabbitmq_user,
        help=f"RabbitMQ username (default: {rabbitmq_user})"
    )
    parser.add_argument(
        "--password",
        type=str,
        default=rabbitmq_password,
        help="RabbitMQ password (default: from environment)"
    )
    parser.add_argument(
        "--queue",
        type=str,
        default=rabbitmq_queue,
        help=f"RabbitMQ queue name (default: {rabbitmq_queue})"
    )
    parser.add_argument(
        "--vhost",
        type=str,
        default=rabbitmq_vhost,
        help=f"RabbitMQ virtual host (default: {rabbitmq_vhost})"
    )
    parser.add_argument(
        "--use-ssl",
        action="store_true",
        default=rabbitmq_use_ssl,
        help="Use SSL for RabbitMQ connection"
    )
    
    args = parser.parse_args()
    
    # If AMQP URL is provided, parse it and use those values
    amqp_config = {}
    if args.amqp_url:
        amqp_config = parse_amqp_url(args.amqp_url)
        if amqp_config:
            print(f"Using AMQP URL: {args.amqp_url}")
            
    # Use values from AMQP URL if available, otherwise use command line args
    host = amqp_config.get('host', args.host)
    port = amqp_config.get('port', args.port)
    user = amqp_config.get('username', args.user)
    password = amqp_config.get('password', args.password)
    vhost = amqp_config.get('vhost', args.vhost)
    use_ssl = amqp_config.get('use_ssl', args.use_ssl)
    
    success = send_message(
        args.url,
        host,
        port,
        user,
        password,
        args.queue,
        vhost,
        use_ssl
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
