#!/usr/bin/env python3
from typing import Dict, Any

from fastapi import FastAPI
from .models import DownloadRequest, VideoDownloadRequest, AudioDownloadRequest, PictureDownloadRequest
from .routes import download_media, download_video, download_audio, download_picture

# FastAPI app
app = FastAPI(
    title="Media Downloader API",
    description="API for downloading media from URLs and processing RabbitMQ messages",
    version="1.0.0"
)

# Define routes
@app.post("/download/", response_model=Dict[str, Any])
async def download_endpoint(request: DownloadRequest) -> Dict[str, Any]:
    """Download media from the provided URL (legacy endpoint)."""
    return await download_media(request)

@app.post("/download/video", response_model=Dict[str, Any])
async def download_video_endpoint(request: VideoDownloadRequest) -> Dict[str, Any]:
    """Download video from the provided URL with organized folder structure."""
    return await download_video(request)

@app.post("/download/audio", response_model=Dict[str, Any])
async def download_audio_endpoint(request: AudioDownloadRequest) -> Dict[str, Any]:
    """Download audio from the provided URL with organized folder structure."""
    return await download_audio(request)

@app.post("/download/picture", response_model=Dict[str, Any])
async def download_picture_endpoint(request: PictureDownloadRequest) -> Dict[str, Any]:
    """Download picture/thumbnail from the provided URL."""
    return await download_picture(request)
