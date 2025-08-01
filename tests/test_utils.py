#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the utility functions
from src.utils import sanitize_filename

def test_sanitize_filename_normal():
    """Test sanitizing a normal filename."""
    result = sanitize_filename("test.mp4")
    assert result == "test.mp4"

def test_sanitize_filename_special_chars():
    """Test sanitizing a filename with special characters."""
    result = sanitize_filename("test: file?.mp4")
    assert result == "test_ file_.mp4"

def test_sanitize_filename_max_length():
    """Test sanitizing a filename that exceeds the max length."""
    long_name = "a" * 300 + ".mp4"
    result = sanitize_filename(long_name, max_length=255)
    assert len(result) <= 255
    assert result.endswith(".mp4")

def test_sanitize_filename_no_extension():
    """Test sanitizing a filename without an extension."""
    result = sanitize_filename("no_extension_file")
    assert result == "no_extension_file"

def test_sanitize_filename_unicode():
    """Test sanitizing a filename with Unicode characters."""
    result = sanitize_filename("üñíçödé.mp4")
    assert result == "üñíçödé.mp4"  # Unicode characters should be preserved
