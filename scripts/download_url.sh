#!/bin/bash

# Check if URL is provided
if [ -z "$1" ]; then
  echo "Error: URL is required"
  echo "Usage: $0 <url>"
  exit 1
fi

# The URL to download
URL="$1"

# API endpoint (modify if using a different host/port)
API_ENDPOINT="http://patmos:8000/download/"

echo "Sending download request for: $URL"

# Send request to API
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$URL\"}"

# Check curl exit status
if [ $? -ne 0 ]; then
  echo "Error: Failed to communicate with the API"
  exit 1
fi

echo "Request sent successfully"
