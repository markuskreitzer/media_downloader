#!/usr/bin/env python3
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import yt_dlp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

# Try to import PlexAPI if available
try:
    from plexapi.server import PlexServer
    PLEX_AVAILABLE = True
except ImportError:
    PLEX_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup error log file
error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler("download_errors.log")
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

# FastAPI app
app = FastAPI(title="Media Downloader API")

# Global configuration
download_dir: Path = Path("./.downloads")
plex_server: Optional[PlexServer] = None
plex_library: str = "Home Videos"


class DownloadRequest(BaseModel):
    url: HttpUrl


def setup_plex() -> Optional[PlexServer]:
    """Connect to Plex server if configuration is available."""
    if not PLEX_AVAILABLE:
        return None
    
    plex_url = os.environ.get("PLEX_URL")
    plex_token = os.environ.get("PLEX_TOKEN")
    
    if not plex_url or not plex_token:
        logger.warning("Plex URL or token not configured. Skipping Plex integration.")
        return None
    
    try:
        return PlexServer(plex_url, plex_token)
    except Exception as e:
        logger.error(f"Failed to connect to Plex server: {e}")
        return None


def trigger_plex_scan() -> bool:
    """Trigger Plex to scan for new files."""
    global plex_server, plex_library
    
    if not plex_server:
        return False
    
    try:
        # Find the appropriate library
        library = next((section for section in plex_server.library.sections() 
                       if section.title == plex_library), None)
        
        if not library:
            logger.warning(f"Library '{plex_library}' not found in Plex server")
            return False
            
        # Update the library to scan for new files
        library.update()
        logger.info(f"Triggered Plex library scan for {plex_library}")
        return True
    except Exception as e:
        logger.error(f"Failed to trigger Plex library scan: {e}")
        return False


@app.post("/download/", response_model=Dict[str, str])
async def download_media(request: DownloadRequest) -> Dict[str, str]:
    """Download media from the provided URL using yt-dlp."""
    url = str(request.url)
    
    # Configure yt-dlp options
    ydl_opts = {
        'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
    }
    
    try:
        # Download the media
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file_path = Path(filename)
            
        # Try to trigger Plex scan if available
        plex_success = trigger_plex_scan() if plex_server else False
            
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


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Media Downloader API")
    parser.add_argument(
        "--download-dir", 
        type=str, 
        default=os.environ.get("DOWNLOAD_DIR", "./.downloads"),
        help="Directory to save downloaded files (default: ./.downloads or DOWNLOAD_DIR env var)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Set up download directory
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up Plex integration
    plex_server = setup_plex()
    plex_library = os.environ.get("PLEX_LIBRARY", plex_library)
    
    logger.info(f"Starting server, download directory set to: {download_dir}")
    
    # Start the FastAPI server using uvicorn
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


