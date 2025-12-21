#!/usr/bin/env python3
"""
URL extraction utilities for improving RabbitMQ message processing.
This module provides robust URL extraction from various message formats.
"""

import re
import logging
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def extract_urls_from_message(data: dict) -> List[str]:
    """
    Extract URLs from message data using multiple strategies.

    Args:
        data: Parsed JSON message from RabbitMQ

    Returns:
        List of extracted URLs
    """
    urls = []

    # Strategy 1: Direct 'url' field
    if "url" in data and data["url"]:
        urls.append(data["url"])
        logger.debug(f"Found URL in 'url' field: {data['url']}")

    # Strategy 2: 'urls' array field
    if "urls" in data and isinstance(data["urls"], list) and data["urls"]:
        valid_urls = [url for url in data["urls"] if url and isinstance(url, str)]
        if valid_urls:
            urls.extend(valid_urls)
            logger.debug(f"Found URLs in 'urls' field: {valid_urls}")

    # Strategy 3: Extract URLs from 'text' field
    if "text" in data and data["text"]:
        text_urls = extract_urls_from_text(data["text"])
        if text_urls:
            urls.extend(text_urls)
            logger.debug(f"Extracted URLs from 'text' field: {text_urls}")

    # Strategy 4: Look for URLs in other string fields
    for key, value in data.items():
        if key not in ["url", "urls", "text"] and isinstance(value, str):
            text_urls = extract_urls_from_text(value)
            if text_urls:
                urls.extend(text_urls)
                logger.debug(f"Found URLs in '{key}' field: {text_urls}")

    # Remove duplicates and empty strings
    unique_urls = [url for url in urls if url and url.strip()]
    deduped_urls = list(dict.fromkeys(unique_urls))  # Remove duplicates while preserving order

    if deduped_urls:
        logger.info(f"Extracted {len(deduped_urls)} unique URLs: {deduped_urls}")
    else:
        logger.warning("No URLs found in message")

    return deduped_urls


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from text using regex patterns.

    Args:
        text: Text content to search for URLs

    Returns:
        List of found URLs
    """
    if not text:
        return []

    # Comprehensive regex for URL detection
    url_patterns = [
        # Standard HTTP/HTTPS URLs
        r'https?://[^\s<>"\']+',
        # URLs without protocol (common in messages)
        r'(?:^|[\s])www\.[^\s<>"\']+',
        # Common domain patterns
        r'(?:^|[\s])(?:youtube\.com|youtu\.be|open\.spotify\.com|twitter\.com|x\.com)[^\s<>"\']+',
    ]

    urls = []
    for pattern in url_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up the URL
            url = match.strip()
            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url
            urls.append(url)

    return urls


def get_primary_url(urls: List[str], prefer_youtube: bool = True) -> Optional[str]:
    """
    Get the primary URL from a list, with optional preference for YouTube.

    Args:
        urls: List of URLs to choose from
        prefer_youtube: Whether to prefer YouTube URLs

    Returns:
        The best URL from the list or None if empty
    """
    if not urls:
        return None

    if prefer_youtube:
        # Prefer YouTube URLs if available
        for url in urls:
            if any(domain in url.lower() for domain in ["youtube.com", "youtu.be"]):
                return url

    # Return first URL by default
    return urls[0]


def clean_url(url: str) -> str:
    """
    Clean up a URL by removing common issues.

    Args:
        url: URL to clean

    Returns:
        Cleaned URL
    """
    if not url:
        return url

    # Remove trailing punctuation and characters
    cleaned = url.rstrip(".,;:!?)")

    # Handle URL encoding issues
    try:
        parsed = urlparse(cleaned)
        # Reconstruct URL with properly encoded query parameters
        if parsed.query:
            # Keep the original path but ensure proper encoding
            cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                cleaned += f"?{parse_qs(parsed.query, doseq=True)}"
        return cleaned
    except Exception:
        logger.warning(f"Failed to parse URL: {cleaned}")
        return cleaned


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formatted and looks downloadable.

    Args:
        url: URL to validate

    Returns:
        True if URL appears valid, False otherwise
    """
    if not url:
        return False

    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        # Check for common downloadable domains
        valid_domains = [
            "youtube.com",
            "youtu.be",
            "open.spotify.com",
            "spotify.com",
            "twitter.com",
            "x.com",
            "vimeo.com",
            "dailymotion.com",
            "facebook.com",
            "instagram.com",
            "tiktok.com",
        ]

        domain = parsed.netloc.lower()
        return any(valid in domain for valid in valid_domains)

    except Exception:
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test cases based on actual log patterns
    test_messages = [
        {"url": "https://youtu.be/abDz5ny9YvI?si=XLRi2RBe4Y3Omf6R", "media_type": "video"},
        {"text": "Check out this video: <https://www.youtube.com/watch?v=example>", "urls": []},
        {"text": "Great song: <https://open.spotify.com/track/example>", "urls": ["https://open.spotify.com/track/example"]},
        {"text": "Multiple links: https://youtu.be/abc and https://youtu.be/def", "urls": []},
        {"text": "Random text without URLs", "urls": []},
    ]

    for i, message in enumerate(test_messages):
        print(f"Test {i + 1}: {message}")
        urls = extract_urls_from_message(message)
        primary_url = get_primary_url(urls)
        print(f"  Extracted URLs: {urls}")
        print(f"  Primary URL: {primary_url}")
        print()
