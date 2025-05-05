#!/usr/bin/env python3
import subprocess
from pathlib import Path
from typing import Dict

import yt_dlp
from fastapi import HTTPException

from .config import logger, error_logger, download_dir, plex_server
from .models import DownloadRequest
from .utils import sanitize_filename
from .plex import trigger_plex_scan


async def download_media(request: DownloadRequest) -> Dict[str, str]:
    """Download media from the provided URL using yt-dlp."""
    url = str(request.url)
    logger.info(f"URL: {request.url}")
    logger.info(request)
    
    # Configure yt-dlp options
    ydl_opts = {
        'outtmpl': str(download_dir / '%(title).50s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
    }
    
    try:
        # Download the media
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            logger.info(f"INFO: {info}")
            filename = ydl.prepare_filename(info)
            file_path = Path(filename)
            
            # Sanitize the filename and rename if necessary
            sanitized_path = Path(file_path.parent) / sanitize_filename(file_path.name)
            if sanitized_path != file_path and file_path.exists():
                file_path.rename(sanitized_path)
                file_path = sanitized_path
            
            # Change file permissions to 777 for NAS share compatibility
            if file_path.exists():
                subprocess.run(['chmod', '777', str(file_path)], check=True)
                logger.info(f"Changed permissions to 777 for {file_path}")
            
        # Try to trigger Plex scan if available
        plex_success = trigger_plex_scan(plex_server) if plex_server else False
            
        return {
            "status": "success",
            "message": f"Downloaded media from {url}",
            "file_path": str(file_path),
            "plex_scan": "success" if plex_success else "skipped"
        }
    except yt_dlp.utils.DownloadError as e:
        # Log the error to the error log file
        error_logger.error(f"Error downloading {url}: {str(e)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download media: {str(e)}"
        )
    except Exception as e:
        # Log the error to the error log file
        error_logger.error(f"Unexpected error downloading {url}: {str(e)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
