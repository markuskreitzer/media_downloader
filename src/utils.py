#!/usr/bin/env python3
import re
import unicodedata

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to contain only UTF-8 characters and limit length.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length (default: 255 for most filesystems)
        
    Returns:
        Sanitized filename
    """
    # Normalize Unicode characters
    filename = unicodedata.normalize('NFC', filename)

    # Replace problematic characters with underscores
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)

    # Ensure the filename isn't too long (accounting for extension)
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) > 1:
        name, ext = name_parts
        # Truncate the name part, preserving the extension
        if len(filename) > max_length:
            max_name_length = max_length - len(ext) - 1  # -1 for the dot
            name = name[:max_name_length]
            filename = f"{name}.{ext}"
    else:
        # No extension, just truncate
        filename = filename[:max_length]

    return filename
