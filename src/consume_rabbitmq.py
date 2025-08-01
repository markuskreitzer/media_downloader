import json
import logging
import os
import ssl
from typing import Any
import pika

logging.basicConfig(level=logging.INFO)


RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5671"))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "guest")
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "/") # Default to root vhost
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'music')

# --- Set to False during testing if you DON'T want to delete messages ---
# --- Set to True for normal operation to remove processed messages ---
ACKNOWLEDGE_MESSAGES = True

def process_message(ch: Any, method: Any, properties: Any, body: bytes) -> None:
    """Callback function executed when a message is received."""
    print(f" [x] Received message from queue '{QUEUE_NAME}'")
    print(f"     Delivery Tag: {method.delivery_tag}")
    print(f"     Properties: {properties}")

    try:
        # Decode message body (assuming UTF-8 encoding)
        message_str = body.decode('utf-8')
        print(f"     Raw Body: {message_str}")

        # Parse the JSON message
        message_data = json.loads(message_str)
        print(f"     Parsed Data: {message_data}")

        # ---> Add your message processing logic here <---
        # For example, access parts of the message:
        # original_text = message_data.get('text')
        # urls = message_data.get('urls', [])
        # print(f"     Extracted URLs: {urls}")

        print(" [x] Done processing.")

        if ACKNOWLEDGE_MESSAGES:
            # Acknowledge the message, telling RabbitMQ it can be deleted
            print(f" [>] Acknowledging message (tag: {method.delivery_tag})...")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("     Message acknowledged.")
        else:
            print(" [!] Message NOT acknowledged (ACKNOWLEDGE_MESSAGES is False).")
            # If you don't ack, the message will remain unacknowledged.
            # If this consumer disconnects, RabbitMQ will re-queue it.

    except json.JSONDecodeError:
        print(f" [!] Error: Could not decode JSON: {body.decode('utf-8', errors='replace')}")
        # Decide how to handle invalid messages:
        # Option 1: Reject and discard
        # ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        # Option 2: Reject and requeue (careful, could cause infinite loop if always failing)
        # ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
        # Option 3: Nack (similar options as reject)
        # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        # For now, we just print error and DO NOT ACK, leaving it unacknowledged
        print(" [!] Message NOT acknowledged due to JSON error.")
    except Exception as e:
        print(f" [!] An unexpected error occurred during processing: {e}")
        # Depending on the error, decide whether to ack, nack, or reject.
        # For safety during unknown errors, we won't ack here.
        print(" [!] Message NOT acknowledged due to processing error.")


def pull_from_rabbitmq(host: str, port: int, vhost: str, username: str, password: str, queue: str, ack_messages: bool = True) -> None:
    """Connects to RabbitMQ and consumes messages from the specified queue."""
    global ACKNOWLEDGE_MESSAGES
    ACKNOWLEDGE_MESSAGES = ack_messages # Use the flag passed to the function

    credentials = pika.PlainCredentials(username, password)
    # Ensure SSL options if using port 5671 (amqps)
    ssl_options = pika.SSLOptions(context=ssl.create_default_context()) if port == 5671 else None
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        virtual_host=vhost,
        credentials=credentials,
        ssl_options=ssl_options # Add this line for AMQPS
        # heartbeat=600, # Example: Increase heartbeat interval
        # blocked_connection_timeout=300 # Example: Increase timeout
    )

    connection = None
    try:
        print(f" [*] Attempting to connect to RabbitMQ at {host}:{port} (vhost: {vhost})...")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        print(" [*] Connection successful. Channel opened.")

        # Declare the queue - idempotent operation.
        # Ensures the queue exists. Must match producer's declaration (durable=True).
        channel.queue_declare(queue=queue, durable=True)
        print(f" [*] Queue '{queue}' declared (or confirmed existing).")

        # Set Quality of Service (QoS) - Optional but recommended
        # This tells RabbitMQ not to send more than 1 message to this worker
        # until the worker has acknowledged the previous one. Prevents overwhelming
        # a single slow consumer.
        channel.basic_qos(prefetch_count=1)

        # Set up the consumer
        # auto_ack=False requires explicit acknowledgement
        channel.basic_consume(
            queue=queue,
            on_message_callback=process_message,
            auto_ack=False # IMPORTANT: Use manual acknowledgements
        )

        print(f" [*] Waiting for messages in queue '{queue}'. To exit press CTRL+C")
        # Start consuming (this is a blocking call)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f" [!] Connection Error: {e}")
        print("     Check RabbitMQ host, port, credentials, vhost, and network connectivity.")
    except pika.exceptions.ProbableAuthenticationError as e:
         print(f" [!] Authentication Error: {e}")
         print("     Check RabbitMQ username and password.")
    except KeyboardInterrupt:
        print(" [!] User interrupted. Stopping consumer...")
    except Exception as e:
        print(f" [!] An unexpected error occurred: {e}")
    finally:
        if connection and not connection.is_closed:
            print(" [*] Closing RabbitMQ connection...")
            connection.close()
            print(" [*] Connection closed.")
        else:
             print(" [*] Connection already closed or never established.")

if __name__ == "__main__":
    # Set ack_required=False if you want to test WITHOUT deleting messages
    # Set ack_required=True for normal operation
    ack_required = False # CHANGE TO False FOR TESTING WITHOUT DELETION

    pull_from_rabbitmq(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        vhost=RABBITMQ_VHOST,
        username=RABBITMQ_USER,
        password=RABBITMQ_PASS,
        queue=QUEUE_NAME,
        ack_messages=ack_required
    )
