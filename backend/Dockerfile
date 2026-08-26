FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for OpenCV, MediaPipe, ffmpeg and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 5 -r requirements.txt

# Copy application source code and ML models
COPY app ./app
COPY models ./models

# Create persistent storage directories and assign ownership to non-root user
RUN mkdir -p uploads/videos uploads/frames uploads/analysis/skeleton uploads/analysis/reports && \
    chown -R appuser:appuser /app


# Switch to non-root user
USER appuser

# Expose FastAPI application port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Production command to run the ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]