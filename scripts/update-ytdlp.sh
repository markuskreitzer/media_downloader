#!/bin/bash
# Daily yt-dlp updater for media-downloader
# This script updates yt-dlp to the latest version and restarts the container

set -e  # Exit on any error

LOG_FILE="/var/log/yt-dlp-update.log"
COOKIE_DIR="/app/cookies"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting yt-dlp update check"

# Function to update yt-dlp
update_ytdlp() {
    log "Checking for yt-dlp updates..."
    
    # Get current version
    if command -v yt-dlp &> /dev/null; then
        CURRENT_VERSION=$(yt-dlp --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log "Current yt-dlp version: $CURRENT_VERSION"
    else
        log "yt-dlp not found, installing..."
        pip install --upgrade yt-dlp
        return 0
    fi
    
    # Update to latest version
    log "Updating yt-dlp to latest version..."
    
    # Use pip to update (more reliable than pipx in containers)
    pip install --upgrade yt-dlp
    
    # Verify update
    NEW_VERSION=$(yt-dlp --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log "Updated yt-dlp to version: $NEW_VERSION"
    
    if [ "$CURRENT_VERSION" != "$NEW_VERSION" ]; then
        log "yt-dlp was successfully updated"
        return 1
    else
        log "yt-dlp is already up to date"
        return 0
    fi
}

# Function to restart container if needed
restart_container() {
    log "Restarting media-downloader container..."
    
    # Get current container state
    if docker-compose ps media-downloader --format "{{.State}}" | grep -q "running"; then
        log "Stopping current container..."
        docker-compose stop media-downloader
        
        log "Starting container with updated yt-dlp..."
        docker-compose up -d media-downloader
        
        # Wait a bit for container to start
        sleep 10
        
        # Check if container is running
        if docker-compose ps media-downloader --format "{{.State}}" | grep -q "running"; then
            log "Container successfully restarted"
        else
            log "ERROR: Failed to restart container"
            return 1
        fi
    else
        log "Container not running, starting it..."
        docker-compose up -d media-downloader
        
        sleep 10
        
        if docker-compose ps media-downloader --format "{{.State}}" | grep -q "running"; then
            log "Container successfully started"
        else
            log "ERROR: Failed to start container"
            return 1
        fi
    fi
}

# Function to check cookies
check_cookies() {
    if [ -d "$COOKIE_DIR" ]; then
        if [ -f "$COOKIE_DIR/youtube.txt" ]; then
            # Check if cookies file is not empty and not too old (7 days)
            COOKIE_AGE=$(find "$COOKIE_DIR/youtube.txt" -mtime +7 -print 2>/dev/null | wc -l)
            COOKIE_SIZE=$(stat -c%s "$COOKIE_DIR/youtube.txt" 2>/dev/null || echo "0")
            
            if [ "$COOKIE_SIZE" -gt 100 ] && [ "$COOKIE_AGE" -eq 0 ]; then
                log "YouTube cookies file is present and recent"
            elif [ "$COOKIE_AGE" -gt 0 ]; then
                log "WARNING: YouTube cookies file is $(( COOKIE_AGE / 86400 )) days old - consider refreshing"
            else
                log "WARNING: YouTube cookies file is very small or empty - consider refreshing"
            fi
        else
            log "WARNING: No YouTube cookies file found at $COOKIE_DIR/youtube.txt"
        fi
    else
        log "INFO: Cookies directory not found at $COOKIE_DIR"
    fi
}

# Function to send notification (optional)
send_notification() {
    # You can customize this to send notifications
    # For example, using curl to send to a webhook, or email, etc.
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-Type: application/json' \
             -d "{\"text\":\"yt-dlp updated to $(yt-dlp --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') on media-downloader\"}" \
             "$WEBHOOK_URL" 2>/dev/null || log "Failed to send webhook notification"
    fi
}

# Main execution
main() {
    log "=== yt-dlp Update Script Started ==="
    
    # Check if we're in the correct directory
    if [ ! -f "docker-compose.yml" ]; then
        log "ERROR: docker-compose.yml not found in current directory"
        exit 1
    fi
    
    # Update yt-dlp
    if update_ytdlp; then
        log "yt-dlp was updated, restarting container..."
        
        # Restart container to apply changes
        if restart_container; then
            log "Container successfully restarted with updated yt-dlp"
            
            # Send notification if webhook configured
            send_notification
        else
            log "ERROR: Failed to restart container"
            exit 1
        fi
    else
        log "No yt-dlp update needed"
    fi
    
    # Check cookies status
    check_cookies
    
    log "=== yt-dlp Update Script Completed ==="
}

# Set up log rotation for daily runs
setup_log_rotation() {
    if command -v logrotate &> /dev/null; then
        # Create logrotate config
        cat > /tmp/yt-dlp-update << EOF
$LOG_FILE {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
        
        # Apply logrotate if not already configured
        if ! grep -q "yt-dlp-update" /etc/logrotate.d/* 2>/dev/null; then
            cp /tmp/yt-dlp-update /etc/logrotate.d/
            log "Set up log rotation for yt-dlp-update log"
        fi
        
        rm /tmp/yt-dlp-update
    fi
}

# Check if we have write permissions for log file
if [ ! -w "$(dirname "$LOG_FILE")" ]; then
    LOG_FILE="/tmp/yt-dlp-update.log"
    log "Using fallback log file: $LOG_FILE"
fi

# Setup log rotation
setup_log_rotation

# Run main function
main "$@"

exit 0