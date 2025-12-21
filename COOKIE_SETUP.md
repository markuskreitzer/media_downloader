# YouTube Browser Cookies Setup Guide

This guide will help you extract browser cookies from your browser and configure them for use with yt-dlp in the media-downloader container to fix 403 Forbidden errors.

## Step 1: Extract Browser Cookies

### Option A: Using Browser Extension (Recommended)
1. Install the "Get cookies.txt LOCALLY" browser extension:
   - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbiekiodulhhpehpj
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookiestxt-locally/

2. Go to YouTube and make sure you're logged in
3. Click the extension icon and download `cookies.txt`
4. Save the file somewhere accessible

### Option B: Manual Extraction (Advanced)
1. Open your browser's developer tools (F12)
2. Go to YouTube and make sure you're logged in
3. Open Application/Storage tab → Cookies → https://www.youtube.com
4. Export cookies in Netscape format

## Step 2: Prepare Cookies for Container

Create a `cookies.txt` file in your project directory:

```bash
# Create a cookies directory
mkdir -p ./cookies

# Copy your extracted cookies here
cp /path/to/your/cookies.txt ./cookies/youtube.txt
```

## Step 3: Update Docker Configuration

### Option A: Volume Mount (Recommended)
Update your `docker-compose.yml` to mount the cookies:

```yaml
version: '3.8'
services:
  media-downloader:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./downloads:/downloads
      - ./cookies:/app/cookies:ro  # Add this line
    environment:
      - YOUTUBE_COOKIES_FILE=/app/cookies/youtube.txt
      # ... other environment variables
```

### Option B: Environment Variable (For small setups)
If you have a small cookies file, you can base64 encode it:

```bash
# Encode cookies file
base64 -i cookies/youtube.txt
# Copy the output and add to docker-compose.yml
```

```yaml
environment:
  - YOUTUBE_COOKIES_BASE64=PASTE_BASE64_OUTPUT_HERE
```

## Step 4: Update Application Code

### Create cookies configuration in `src/config.py`:

Add these lines to load cookies:

```python
import os
import base64
from pathlib import Path

# Cookie configuration
YOUTUBE_COOKIES_FILE = os.getenv("YOUTUBE_COOKIES_FILE")
YOUTUBE_COOKIES_BASE64 = os.getenv("YOUTUBE_COOKIES_BASE64")

def get_youtube_cookies_path() -> Optional[str]:
    """Get path to YouTube cookies file."""
    if YOUTUBE_COOKIES_FILE and Path(YOUTUBE_COOKIES_FILE).exists():
        return YOUTUBE_COOKIES_FILE
    
    if YOUTUBE_COOKIES_BASE64:
        # Decode base64 cookies and write to temp file
        cookies_dir = Path("/tmp/cookies")
        cookies_dir.mkdir(exist_ok=True)
        cookies_file = cookies_dir / "youtube.txt"
        
        with open(cookies_file, "wb") as f:
            f.write(base64.b64decode(YOUTUBE_COOKIES_BASE64))
        
        return str(cookies_file)
    
    return None
```

### Update download functions in `src/routes.py`:

Modify the `_download_with_options` function to include cookies:

```python
def _get_ydl_options(media_type: MediaType, output_path: Path) -> dict:
    """Get yt-dlp options for media type."""
    cookies_path = get_youtube_cookies_path()
    
    ydl_opts = {
        'format': 'bestaudio/best' if media_type == MediaType.AUDIO else 'best[height<=720]',
        'outtmpl': str(output_path),
        'writethumbnail': True,
        'writeinfojson': True,
        'extractaudio': True if media_type == MediaType.AUDIO else False,
        'audioformat': 'mp3',
        'audioquality': '0',
        'keepvideo': False,
        'ignoreerrors': True,
        'no_warnings': False,
        'extractflat': False,
        'split_chapters': False,
        'restrictfilenames': True,
    }
    
    # Add cookies if available
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path
        logger.info(f"Using YouTube cookies from: {cookies_path}")
    
    return ydl_opts
```

## Step 5: Update Dockerfile

Ensure the container can write to temp directories:

```dockerfile
FROM python:3.11-slim

# ... existing setup ...

# Create temp directory for cookies
RUN mkdir -p /tmp/cookies && chmod 777 /tmp/cookies

# ... rest of Dockerfile ...
```

## Step 6: Test the Setup

1. Restart your container:
```bash
docker-compose down
docker-compose up -d --build
```

2. Check logs for cookies being loaded:
```bash
docker-compose logs media-downloader | grep "YouTube cookies"
```

3. Test a YouTube URL that was previously failing

## Step 7: Security Considerations

- **Never commit cookies files to git** - they contain authentication tokens
- Add `cookies/` to your `.gitignore`:
```gitignore
cookies/
*.txt
```

- Refresh cookies periodically (they expire)
- Use a dedicated Google account for automated downloads

## Step 8: Cookie Maintenance

### Automatic Cookie Refresh Script
Create a script to refresh cookies monthly:

```bash
#!/bin/bash
# refresh-cookies.sh
echo "Please update your cookies.txt file"
echo "1. Open YouTube in your browser"
echo "2. Export cookies using the browser extension"
echo "3. Replace ./cookies/youtube.txt with the new file"
echo "4. Restart the container: docker-compose restart"

read -p "Press Enter when done..."

# Restart container
docker-compose restart media-downloader
echo "Container restarted with new cookies"
```

Make it executable:
```bash
chmod +x refresh-cookies.sh
```

## Troubleshooting

### Cookies Not Working:
1. Verify the cookies file is accessible in the container
2. Check that cookies are not expired
3. Ensure YouTube account is in good standing
4. Try re-extracting cookies from a fresh browser session

### Still Getting 403 Errors:
1. Check if cookies include YouTube session cookies
2. Verify the file is in proper Netscape format
3. Try using a different browser or incognito mode to extract cookies

### Alternative: Use yt-dlp's Built-in Browser
If cookies don't work, you can configure yt-dlp to use its built-in browser:

```python
ydl_opts.update({
    'extractor_args': {
        'youtube': {
            'player_client': 'ios',
            'player_skip': ['webpage', 'configs'],
        }
    }
})
```

This should resolve most YouTube 403 Forbidden errors you're experiencing!