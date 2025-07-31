#!/usr/bin/env python3
"""
Test script for media downloader endpoints.
"""

import requests
import json
import sys

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"

# Test URLs - replace with actual URLs for testing
TEST_URLS = {
    "video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with actual video URL
    "audio": "https://soundcloud.com/example/track",         # Replace with actual audio URL
    "picture": "https://example.com/image.jpg"               # Replace with actual image URL
}

def test_endpoint(endpoint, url):
    """Test a specific endpoint with a URL."""
    print(f"\nTesting {endpoint} endpoint...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/download/{endpoint}",
            json={"url": url},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {result['message']}")
            print(f"  File: {result['file_path']}")
            if 'metadata' in result:
                print(f"  Metadata: {json.dumps(result['metadata'], indent=2)}")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")

def main():
    """Run tests for all endpoints."""
    print("Media Downloader Endpoint Tests")
    print("=" * 50)
    
    # Test each endpoint
    for media_type, url in TEST_URLS.items():
        if url.startswith("https://example.com") or url.startswith("https://soundcloud.com/example"):
            print(f"\nSkipping {media_type} test - please replace with actual URL")
            continue
        test_endpoint(media_type, url)
    
    # Test legacy endpoint
    print("\nTesting legacy /download/ endpoint...")
    if not TEST_URLS["video"].startswith("https://example.com"):
        test_endpoint("", TEST_URLS["video"])

if __name__ == "__main__":
    main()