#!/usr/bin/env python3
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the application
from src.app import app

client = TestClient(app)

def test_app_startup():
    """Test that the application starts up successfully."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Media Downloader API" in response.text

def test_invalid_url():
    """Test that invalid URLs are rejected."""
    response = client.post(
        "/download/",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 422  # Validation error
