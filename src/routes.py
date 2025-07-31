#!/usr/bin/env python3
import subprocess
from pathlib import Path
from typing import Dict, Optional

import yt_dlp
from fastapi import HTTPException

from .config import logger, error_logger, download_dir, plex_server
from .models import DownloadRequest, VideoDownloadRequest, AudioDownloadRequest, PictureDownloadRequest, MediaType
from .utils import sanitize_filename
from .plex import trigger_plex_scan


def _get_organized_path(info: dict, media_type: MediaType, base_dir: Path) -> Path:
    """
    Organize files based on metadata and media type.
    
    For music/audio: artist/album/title
    For videos: channel/title or channel/series/title
    For pictures: downloads/pictures/
    """
    # Extract metadata
    title = info.get('title', 'Unknown')
    uploader = info.get('uploader', info.get('channel', 'Unknown'))
    artist = info.get('artist', None)
    album = info.get('album', None)
    series = info.get('series', None)
    
    # Sanitize all components
    title = sanitize_filename(title)
    uploader = sanitize_filename(uploader)
    
    if media_type == MediaType.AUDIO or (media_type == MediaType.VIDEO and artist):
        # Music organization: artist/album/title
        artist = sanitize_filename(artist or uploader)
        if album:
            album = sanitize_filename(album)
            return base_dir / "audio" / artist / album / title
        else:
            return base_dir / "audio" / artist / title
    elif media_type == MediaType.VIDEO:
        # Video organization: channel/series/title or channel/title
        if series:
            series = sanitize_filename(series)
            return base_dir / "video" / uploader / series / title
        else:
            return base_dir / "video" / uploader / title
    else:  # MediaType.PICTURE
        return base_dir / "pictures" / title


async def _download_with_options(url: str, media_type: MediaType, ydl_opts: dict) -> Dict[str, str]:
    """Common download logic with specified options."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get metadata
            info = ydl.extract_info(url, download=False)
            logger.info(f"Extracted info for {media_type.value}: {info.get('title', 'Unknown')}")
            
            # Get organized path based on metadata
            organized_dir = _get_organized_path(info, media_type, download_dir)
            organized_dir.mkdir(parents=True, exist_ok=True)
            
            # Update output template with organized path
            ext = info.get('ext', 'mp4' if media_type == MediaType.VIDEO else 'mp3')
            filename = f"{sanitize_filename(info.get('title', 'download'))}.{ext}"
            full_path = organized_dir / filename
            
            # Update options with final path
            ydl_opts['outtmpl'] = str(full_path)
            
            # Download the file
            with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                ydl2.download([url])
            
            # Change file permissions to 777 for NAS share compatibility
            if full_path.exists():
                subprocess.run(['chmod', '777', str(full_path)], check=True)
                logger.info(f"Changed permissions to 777 for {full_path}")
            
            # Try to trigger Plex scan if available
            plex_success = trigger_plex_scan(plex_server) if plex_server else False
            
            return {
                "status": "success",
                "message": f"Downloaded {media_type.value} from {url}",
                "file_path": str(full_path),
                "media_type": media_type.value,
                "metadata": {
                    "title": info.get('title'),
                    "uploader": info.get('uploader'),
                    "artist": info.get('artist'),
                    "album": info.get('album'),
                },
                "plex_scan": "success" if plex_success else "skipped"
            }
    except yt_dlp.utils.DownloadError as e:
        error_logger.error(f"Error downloading {media_type.value} from {url}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download {media_type.value}: {str(e)}"
        )
    except Exception as e:
        error_logger.error(f"Unexpected error downloading {media_type.value} from {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


async def download_video(request: VideoDownloadRequest) -> Dict[str, str]:
    """Download video from the provided URL."""
    url = str(request.url)
    logger.info(f"Downloading video from: {url}")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }
    
    return await _download_with_options(url, MediaType.VIDEO, ydl_opts)


async def download_audio(request: AudioDownloadRequest) -> Dict[str, str]:
    """Download audio from the provided URL."""
    url = str(request.url)
    logger.info(f"Downloading audio from: {url}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }
    
    return await _download_with_options(url, MediaType.AUDIO, ydl_opts)


async def download_picture(request: PictureDownloadRequest) -> Dict[str, str]:
    """Download picture/thumbnail from the provided URL."""
    url = str(request.url)
    logger.info(f"Downloading picture from: {url}")
    
    # For pictures, we'll download the thumbnail or use yt-dlp for image posts
    ydl_opts = {
        'skip_download': False,
        'noplaylist': True,
        'writethumbnail': True,
    }
    
    return await _download_with_options(url, MediaType.PICTURE, ydl_opts)


async def download_media(request: DownloadRequest) -> Dict[str, str]:
    """Download media from the provided URL using yt-dlp (legacy endpoint)."""
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
