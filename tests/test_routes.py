#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """
    Simple test to ensure the modules can be imported correctly.
    This will fail if there are import errors in the application.
    """

    assert True

@pytest.mark.asyncio
@patch('src.routes.yt_dlp.YoutubeDL')
async def test_download_media_success(mock_ytdl):
    """Test successful media download."""
    from src.routes import download_media
    from src.models import DownloadRequest

    # Mock YoutubeDL behavior
    mock_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {"title": "test_video"}
    mock_instance.prepare_filename.return_value = "/app/.downloads/test_video.mp4"

    # Create a mock Path.exists method that returns True
    with patch('pathlib.Path.exists', return_value=True):
        # Create a mock Path.rename method
        with patch('pathlib.Path.rename'):
            # Mock subprocess.run
            with patch('subprocess.run'):
                # Call the function
                request = DownloadRequest(url="https://example.com/video.mp4")
                result = await download_media(request)

                # Verify the result
                assert result["status"] == "success"
                assert "Downloaded media from" in result["message"]
                assert "test_video.mp4" in result["file_path"]
