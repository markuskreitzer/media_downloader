FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./

# Create download directory
RUN mkdir -p /.downloads

# Set environment variables
ENV DOWNLOAD_DIR=/.downloads

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["python", "download_api.py", "--host", "0.0.0.0", "--port", "8000"]
