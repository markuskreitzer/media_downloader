#!/usr/bin/env python3
import os
from typing import Optional

from .config import logger, PLEX_AVAILABLE, plex_library

# Import conditionally based on availability
if PLEX_AVAILABLE:
    from plexapi.server import PlexServer


def setup_plex() -> Optional['PlexServer']:
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


def trigger_plex_scan(plex_server: Optional['PlexServer']) -> bool:
    """Trigger Plex to scan for new files."""
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
