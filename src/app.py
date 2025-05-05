#!/usr/bin/env python3
from typing import Dict

from fastapi import FastAPI
from .models import DownloadRequest
from .routes import download_media

# FastAPI app
app = FastAPI(
    title="Media Downloader API",
    description="API for downloading media from URLs and processing RabbitMQ messages",
    version="1.0.0"
)

# Define routes
@app.post("/download/", response_model=Dict[str, str])
async def download_endpoint(request: DownloadRequest) -> Dict[str, str]:
    """Download media from the provided URL."""
    return await download_media(request)
